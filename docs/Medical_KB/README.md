# Medical Knowledge Base (Medical_KB)

Sample knowledge base for MedAudit RAG. All content is **sample** and can be updated or replaced with institutional guidelines.

## Folder Structure

- **Documentation/** — Scope, policies, audit definitions (e.g. clinical-audit-scope.md).
- **SOPs/** — Standard operating procedures (imaging documentation, handoff/continuity, prediabetes/diabetes follow-up).
- **User_Manuals/** — Platform user guide (MedAudit).
- **FAQs/** — Frequently asked questions about audits and output.

## Use in RAG

- Markdown files are chunked (384–768 tokens), with metadata: document_name, document_type, source.
- Chunks are embedded (e.g. GPT-style embeddings for KB) and stored in Qdrant.
- At audit time, relevant KB chunks are retrieved and passed to MedGemma with EHR context for evidence-based findings.

## Adding or Updating Content

- Add or edit `.md` files under the appropriate folder.
- Re-run the KB indexing step to update the vector store.
