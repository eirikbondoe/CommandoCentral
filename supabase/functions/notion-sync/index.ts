import { Client as NotionClient } from 'npm:@notionhq/client@2.3.0';
import { createClient } from 'jsr:@supabase/supabase-js@2';

type NotionPage = {
  id: string;
  url: string;
  created_time: string;
  last_edited_time: string;
  properties: Record<string, unknown>;
};

const getTitle = (page: NotionPage): string | null => {
  const candidates = Object.values(page.properties) as Array<Record<string, unknown>>;
  for (const prop of candidates) {
    if (prop?.type === 'title' && Array.isArray(prop.title)) {
      const text = prop.title
        .map((item: { plain_text?: string }) => item?.plain_text ?? '')
        .join('')
        .trim();
      if (text) return text;
    }
  }
  return null;
};

const getStatus = (page: NotionPage): string | null => {
  const candidates = Object.values(page.properties) as Array<Record<string, unknown>>;
  for (const prop of candidates) {
    if (prop?.type === 'status' && prop.status && typeof prop.status === 'object') {
      return (prop.status as { name?: string }).name ?? null;
    }
    if (prop?.type === 'select' && prop.select && typeof prop.select === 'object') {
      return (prop.select as { name?: string }).name ?? null;
    }
  }
  return null;
};

const getTags = (page: NotionPage): string[] => {
  const candidates = Object.values(page.properties) as Array<Record<string, unknown>>;
  for (const prop of candidates) {
    if (prop?.type === 'multi_select' && Array.isArray(prop.multi_select)) {
      return prop.multi_select
        .map((item: { name?: string }) => item?.name)
        .filter((value): value is string => Boolean(value));
    }
  }
  return [];
};

const chunk = <T>(items: T[], size: number): T[][] => {
  const result: T[][] = [];
  for (let index = 0; index < items.length; index += size) {
    result.push(items.slice(index, index + size));
  }
  return result;
};

Deno.serve(async () => {
  try {
    const notionApiKey = Deno.env.get('NOTION_API_KEY');
    const notionDatabaseId = Deno.env.get('NOTION_DATABASE_ID');
    const ownerId = Deno.env.get('NOTION_SYNC_OWNER_ID');
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseServiceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!notionApiKey || !notionDatabaseId || !ownerId || !supabaseUrl || !supabaseServiceRoleKey) {
      return new Response(
        JSON.stringify({
          error:
            'Missing one or more required secrets: NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_SYNC_OWNER_ID, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY',
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } },
      );
    }

    const notion = new NotionClient({ auth: notionApiKey });
    const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

    const pages: NotionPage[] = [];
    let cursor: string | undefined;

    do {
      const response = await notion.databases.query({
        database_id: notionDatabaseId,
        start_cursor: cursor,
      });

      for (const result of response.results) {
        if (result.object === 'page') {
          pages.push(result as unknown as NotionPage);
        }
      }

      cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
    } while (cursor);

    const upsertRows = pages.map((page) => ({
      owner_id: ownerId,
      notion_page_id: page.id,
      notion_database_id: notionDatabaseId,
      title: getTitle(page),
      status: getStatus(page),
      tags: getTags(page),
      notion_url: page.url,
      created_time: page.created_time,
      last_edited_time: page.last_edited_time,
      raw_properties: page.properties,
      raw_page: page,
      synced_at: new Date().toISOString(),
    }));

    for (const batch of chunk(upsertRows, 100)) {
      const { error } = await supabase
        .from('notion_pages')
        .upsert(batch, { onConflict: 'owner_id,notion_page_id' });

      if (error) {
        throw error;
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        fetched: pages.length,
        upserted: upsertRows.length,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    );
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown notion sync error',
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } },
    );
  }
});
