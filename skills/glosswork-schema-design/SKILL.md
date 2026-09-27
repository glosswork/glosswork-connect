---
name: glosswork-schema-design
description: Glosswork's guidance for designing a schema in a Glosswork workspace, covering object types, fields, select options, relations, and the descriptions agents read later. Use it when a person wants to start tracking something in Glosswork, asks you to build, extend, or reshape a Glosswork schema, or before you call create_object_type, add_field, update_field, or propose_schema_change.
---

# Designing a Glosswork schema

You are about to turn what your human wants to keep track of into object types and fields. This is Glosswork's view of what a good schema looks like. Other agents will read what you write later, in other tools, with only your names and descriptions to go on. So aim for a schema that is small, uses real types, and is described well. It does not have to be perfect: changing it later is normal and cheap.

## Before you create anything

- **You need an `admin` token.** `create_object_type`, `add_field`, and the other schema tools are listed only for an `admin`-scope token. If you cannot see `create_object_type`, tell your human the connection needs an admin token. Do not look for another way in.
- **Read `describe_capabilities` and `list_object_types`** if you have not already this session.
- **Ask what they will want to ask of it.** "What questions do you want this to answer?" A good schema answers each one with a single `query_records` filter. If a question needs a fact the schema would not hold, such as a last-contacted date, that fact needs a field. If it does not, the question gets answered by guesswork.

## Five rules

**1. Start small. Do not create eleven fields when four will do.** For a first object type, create only the fields your human named and the fields their questions need. That is usually four to six. Leave out anything that seems nice to have. Adding a field later takes effect at once and needs nobody's approval. Removing one needs a human to approve it. So too few fields is the cheap mistake, and too many is the expensive one. A small schema is also one your human can take in when you show it to them.

**2. Prefer a select over free text.** When a value comes from a short, known list (a stage, a status, a priority, a category), make it a `single_select`, or a `multi_select` for tags where a record can have several. Every option needs a `value`, a `label`, and a `description`. A select filters exactly, with no misspellings, and a `single_select` is indexed automatically. Keep free text for values that really vary, such as names and notes. Adding an option later takes effect at once. Removing one that records still use becomes a proposal a human approves.

**3. Prefer a relation over a repeated string.** When the same thing would be typed into many records (a company, a project, a contact) or has facts of its own, make it its own object type and link to it with a `relation` field. Use a relation only where two things really are different things; a status or a date is not a thing. Mechanics:
- Create the target type first. A relation can point only at a type that already exists, or at the type you are creating, by its key.
- Set `config.cardinality` to `one` or `many`, and set `config.inverse_field_key` so the target type gets a field linking back.
- A relation cannot be required, unique, or defaulted. Its values are set with `link_records`, never in `values`.
- `user_ref` is only for people who have an account in this workspace. For an outside contact who never signs in, use text or a type of their own.

**4. Write every description for the agent that reads it next.** Descriptions are required on the type, on every field, and on every select option, and an empty one is refused. A description that just repeats the name tells the next agent nothing. Say:
- For a type: what one record is, and when to create a new record rather than update an existing one.
- For a field: what the value means, when to set or change it, its unit or currency, and what an empty value means.
- For an option: what has to be true for a record to be in it, and how it differs from the option next to it.

Weak: `stage`: "The stage." Strong: `stage`: "Where this pitch sits in the sales pipeline. Move it forward when the client responds; set lost when they decline or stop replying for good."

**5. Use the real type.** Use `date` or `datetime` for anything that is a date, so a filter such as `{"field": "next_follow_up", "op": "lt", "value": "@today"}` works without your computing a date. Use `integer` or `decimal` for amounts and counts, with the unit in the description; `boolean` for yes or no; `url` for links; `long_text` for notes, which also take part in semantic search by default. Choose carefully, because changing a field's type later always becomes a proposal a human approves, and a field cannot be changed into a `relation` or an `attachment` at all.

## Keys, names, and the rest

- **Keys are permanent.** The type key, every field key, and the `key_prefix` are lowercase snake_case (the prefix is 2 to 10 uppercase letters and digits, starting with a letter) and cannot be changed after creation. `key_prefix` `PROS` gives records the keys `PROS-001`, `PROS-002`. Names and descriptions can be edited at any time.
- **Do not add fields the system already keeps.** Every record already has `key`, `created_at`, `updated_at`, `created_by`, `updated_by`, `comment_count`, and `last_comment_at`, and filters can use them. These names are reserved for field keys (read `key_rules.reserved_field_keys`). If you need a similar field, add a suffix: `created_by_name` is accepted.
- **Pick the display field** (`display_field_key`): the field a person recognizes a record by, usually a name. It cannot be a relation, `user_ref`, or attachment field. If you leave it out, the first eligible field is used.
- **Use `required` sparingly,** only where a record makes no sense without the value. Making a field required later takes effect at once if every record already has a value, and becomes a proposal if some do not.
- **Set `indexed`** on a text or number field you expect to filter or sort by often. Select, date, datetime, and user_ref fields are indexed already.

## Build it

Create the type and its fields in one `create_object_type` call, with `fields` and `display_field_key`. The call returns the full description of the type; read it back to check what you built. If a call is refused, the error names what to fix and often the tool to call next. Correct the call; do not repeat it unchanged.

## Show your human what you built

- List each field with its type and the description you wrote, and each select's options with their descriptions. The descriptions are the part that lets any agent use this later, so do not skip them.
- Tell them: adding types, fields, and options takes effect immediately. Deleting a field or a type, changing a field's type, or removing an option that records use becomes a proposal they approve in the Glosswork web UI. You cannot approve it, so you cannot delete their data without them.
- Offer to enter their first few records. Use the exact option values from the type's description, and link related records with `link_records`.

## When they want to change it later

- Additive changes apply immediately: `add_field`, adding options with `update_field`, and renaming or re-describing with `update_field` or `update_object_type`.
- A destructive `update_field` change comes back `pending_human_approval` with a proposal id, and nothing changes until a human approves it. `delete_field` and `delete_object_type` go through `propose_schema_change`, with a `reason` the approving human will read. Send each destructive change in its own call, apart from additive changes.
- Tell your human a proposal is waiting and where to approve it. Check its status later with `list_schema_proposals`.
- Do not work around a proposal. For example, do not add a replacement field and stop using the old one without telling your human.
- If you cannot see `create_object_type` or `add_field` at all, you are not connected with an `admin` token. Tell your human.
