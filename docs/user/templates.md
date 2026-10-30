# Overriding templates

Chancellor renders records with Jinja2 templates. It ships a built-in template set and lets a
repository override individual templates with its own. This page explains where the built-in
templates live, how a repository provides overrides, and how chancellor chooses between them.

## Reading other records

A template sees its own record's data, `data_hash`, the record set's version as `meta.version`, the
record's `absolute_id`, and under `refs.<field>` what each reference field declares with `depends`:
the ID only (`id`, the default), also the target document's `file_name`, `path` and `absolute_id`
(`name`), or also the target's data (`data`). A template cannot read more than that, and a document
rebuilds exactly when what it reads changes. Data references reach one hop: references inside a
target's data are IDs only. Following chains of data references is deferred to a later version.

## References to other records

A reference field holds record IDs, such as `addresses: [R0001]`. A bare ID means the current
version of the record set, and so does an absolute ID of the current version (`0.1.0:R0001`).
Chancellor checks every such value against the current records and fails the build when one names no
record. An absolute ID of an older version is a historic reference: it is not checked, and the build
warns about it. In `refs.<field>`, every entry carries `historic` and `version`; for a historic
reference whose ID still exists, `current` holds that record's `id`, `file_name`, `path` and
`absolute_id`, so a template can link to it or mark the reference as outdated.

A reference to something outside the project must never look like a local ID: write it as
`<project>:<version>:<id>`, such as `other-project:1.0.0:D0001`, or as a URL. An external reference
that looks like an internal one would be easy to misread, and a typo in an internal one would go
unnoticed.
