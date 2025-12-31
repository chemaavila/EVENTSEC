# EventSec Documentation - Threat Intelligence Section Design

This page captures the intended look & feel for the Threat Intelligence tab you shared, plus ideas for how it would integrate into the EventSec UI.

## Layout Overview

1. **Header bar** – Mirror the mockup with breadcrumb-style text (`SIEM Dashboard / Threat Intelligence`), a bold title, subtitle, and an “Actualizar” button plus “Última actualización” indicator.
2. **KPI cards** – Four cards summarizing key metrics (processed emails, blocked threats, VIP users attacked, active DLP rules). Each card should include:
   - Icon (email shield, shield, user, badge)
   - Numeric value and relative trend text (e.g., `+5.2%`)
   - Status tag (e.g., “Activo”) if appropriate.
3. **Tab strip** – Provide tabs (“Cuarentena”, “Informes”, “Políticas”, “Búsqueda de mensajes”, “Suplantación”). Tabs toggle the dataset rendered below.
4. **Filters row** – Under the tabs add controls: search input (subject/remitente), time range dropdown, threat type dropdown, plus action buttons (“Exportar”, “Liberar selección”, “Actualizar”).
5. **Results table** – Table columns: Fecha, Puntuación (with a pill and numeric score), Remitente/Destinatario, Asunto, Tipo (tag), Acciones (buttons/links). Add pagination at the bottom.
6. **Footer summary** – Show total rows (e.g., “Mostrando 1-12 de 142”) plus Prev/Next controls matching the screenshot.

## Data & Behavior

- Default tab = “Cuarentena”. Each row links to the threat details (war room note or email object).
- “Acciones” column could offer quick actions (release, escalate, view context).
- “Tipo” tags (Phishing, Malware, Spam, Spoofing) use color-coded pills for readability.
- Filtering updates the dataset via `/email-protection/sync` results or cached records.
- The “Actualizar” button re-triggers a sync (calls `/sync/google` or `/sync/microsoft` depending on how the email protection service is configured) and refreshes the table/timestamp.

## Next Steps

1. Implement the Threat Intelligence page under `frontend/src/pages/ThreatIntelPage.tsx` with mock data to match this layout.
2. Add icons + cards at the top, reuse the style classes introduced in `EmailProtectionPage`.
3. Hook the tab controls to filter states and integrate with the Email Protection API once tokens exist.
4. Add a sidebar entry if necessary, similar to the Email Protection connector.

Let me know if you’d like me to also craft the API contract or backend storage needed for the quarantined messages table; we can reuse the Email Protection service’s findings feed as the data source.


