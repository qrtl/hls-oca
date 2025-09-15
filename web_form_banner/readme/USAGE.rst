#. Go to *Settings > Tachnical > User Interface > Form Banner Rules* and create a rule.
#. Choose Model, (optionally) restrict Form Views, set Default Severity, Target XPath
   (insertion point), Position, and configure the message.
#. Save. Open any matching form record—the banner will appear and auto-refresh after
   load/save/reload.

Usage of message fields:
~~~~~~~~~~~~~~~~~~~~~~~~

* **Message** (message): Text shown in the banner. Supports `${placeholders}` filled
  from values returned by message_value_code. Ignored if message_value_code returns an
  `html` value.
* **HTML** (message_is_html): If enabled, the message string is rendered as HTML;
  otherwise it's treated as plain text.
* **Message Value Code** (message_value_code): Safe Python expression evaluated per
  record. Return a dict such as `{"visible": True, "severity": "warning", "values": {"name": record.name}}`.
  Use either message or `html` (from this code), not both. Several evaluation context
  variables are available.

Evaluation context variables available in Message Value Code:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `env`: Odoo environment for ORM access.
* `user`: Current user (`env.user`).
* `ctx`: Copy of the current context (`dict(env.context)`).
* `record`: Current record (the form's record).
* `model`: Shortcut to the current model (`env[record._name]`).
* `url_for(obj)`: Helper that returns a backend form URL for `obj`.
* `context_today(ts=None)`: User-timezone “today” (date) for reliable date comparisons.
* `time`, `datetime`: Standard Python time/datetime modules.
* `dateutil`: `{ "parser": dateutil.parser, "relativedelta": dateutil.relativedelta }`
* `timezone`: `pytz.timezone` for TZ handling.
* `float_compare`, `float_is_zero`, `float_round`: Odoo float utils for precision-safe
  comparisons/rounding.

All of the above are injected by the module to the safe_eval locals.

Message setting examples:
~~~~~~~~~~~~~~~~~~~~~~~~~

**A) Missing email on contact (warning)**

* Model: `res.partner`
* Message: `This contact has no email.`
* Message Value Code:

.. code-block:: python

  {"visible": not bool(record.email)}

**B) Show partner comment if available**

* Model: `purchase.order`
* Message: `Vendor Comments: ${comment}`
* Message Value Code (single expression):

.. code-block:: python

  {
    "visible": bool(record.partner_id.comment),
    values: {"comment": record.partner_id.comment},
  }

It is also possible to use "convenience placeholders" without an explicit `values` key:

.. code-block:: python

  {
    "visible": bool(record.partner_id.comment),
    "comment": record.partner_id.comment,
  }

**C) High-value sale order (dynamic severity)**

* Model: `sale.order`
* Message: `High-value order: ${amount_total}`
* Message Value Code:

.. code-block:: python

  {
    "visible": record.amount_total > 30000,
    "severity": "danger" if record.amount_total >= 100000 else "warning",
    "values": {"amount_total": record.amount_total},
  }

**D) Quotation past validity date**

* Model: `sale.order`
* Message: `This quotation is past its validity date (${validity_date}).`
* Message Value Code:

.. code-block:: python

  {
    "visible": bool(record.validity_date and context_today() > record.validity_date and record.state in ["draft", "sent"]),
    "values": {"validity_date": record.validity_date},
  }

**E) Pending activities on a task (uses env)**

* Model: `project.task`
* Message: `There are ${cnt} pending activities.`
* Message Value Code (multi-line with `result`):

.. code-block:: python

  cnt = env["mail.activity"].search_count([("res_model","=",record._name),("res_id","=",record.id)])
  result = {"visible": cnt > 0, "values": {"cnt": cnt}}

**F) HTML banner linking to the customer's last sales order**

* Model: `sale.order`
* Message: (leave blank; `html` provided by Message Value Code)
* Message Value Code (multi-line with `result`):

.. code-block:: python

  last = model.search(
    [("partner_id", "=", record.partner_id.id), ("id", "<", record.id)],
    order="date_order desc, id desc",
    limit=1,
  )
  if last:
    html = "<strong>Previous order:</strong> <a href='%s'>%s</a>" % (url_for(last), last.name)
    result = {"visible": True, "html": html}
  else:
    result = {"visible": False}
