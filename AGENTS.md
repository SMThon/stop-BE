<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

## What Lovable manages

Rules outside this block are the project's own. Change the pieces below in
Lovable, not by hand. With the [Lovable MCP](https://mcp.lovable.dev)
connected, `send_message` asks Lovable to do it; otherwise ask the user to
use the editor.

- **Database.** Do not add or edit `supabase/migrations/` or `drizzle/`.
  Ask Lovable to change the schema.
- **Generated files.** Do not edit a file whose header says it is automatically
  generated.
- **AI gateway.** Keep model calls on Lovable's gateway, and keep
  `LOVABLE_API_KEY` out of browser code.
- **Connectors.** Lovable provides native connectors. `list_connectors` shows
  which are enabled; `add_connector` only returns the dashboard link. When a
  connector is enabled, calls go through the connector gateway and need
  `LOVABLE_API_KEY`. When Lovable does not provide one, users can bring their
  own key and store it in Secrets.
- **Secrets.** Lovable manages them. Do not put secret values in the repo.
<!-- LOVABLE:END -->

## Data architecture
- Keep normalized service data and date-only calculations in browser-safe `src/data` modules; no persistence or network fetching is needed to consume the datasets.
- Keep the legacy refund dataset compatible and put new normalized records in separate modules, so existing consumers are not silently broken.
- Store source verification separately from drafting/access attempts and gate preset price autofill on verification, so unconfirmed candidates cannot become confirmed facts.
- Use the official-source verified catalog for user-facing refund guidance and normalized active lists; isolate legacy rules and draft presets from it so compatibility data cannot be mistaken for verified guidance.
- Keep each verified rule's period unit, date basis, conditions, scope and source references explicit; date-only calculations cannot approve refunds or evaluate hour-based limits.
- Generate demo dates from an explicit reference date and mark demo data as fictional, so presentation timing remains reproducible without pretending to be collected data.
- Calculate date-only deadlines in UTC with validated ISO dates and preserve billing anchors across month-end adjustments, so time zones and short months do not shift results.
