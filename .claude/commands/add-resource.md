---
description: Scaffold a complete new REST resource vertical slice. Usage /add-resource <name>
argument-hint: <resource-name-singular>
---

Scaffold a new resource named **$ARGUMENTS** across every layer of this FastAPI
app, following the `scaffold-resource` skill exactly (read it first if needed).

Use the `api-designer` subagent for the design, or do it inline if the resource
is simple. The `products` resource is the reference implementation — match its
conventions for models, schemas, repository, service, router, deps wiring, and
tests. When done, run `python3 -m compileall app tests` and remind me to run
`make revision m="add $ARGUMENTS"`.
