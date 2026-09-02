Odoo's `phone_validation` always reformats contacts' phone and mobile numbers
in international format, prepending the country code (e.g.
`+81 90-1234-5678`). This module makes the format configurable per company:

- **As entered**: no formatting is applied.
- **National**: without the country code (e.g. `090-1234-5678`).
- **International**: with the country code (e.g. `+81 90-1234-5678`) - Odoo's
  default behavior.

When *National* is selected, contacts located in a different country from the
company are still formatted in *International*, as a national format is not
meaningful without its own country code.
