# Deployment notes (AWS phase)

This project runs locally with `docker compose`. The AWS phase moves the same
pieces into managed cloud services. This file is a checklist, not a script -
follow it when you reach Phase 10.

## Mapping: local -> AWS

| Local (docker-compose)        | AWS service                     |
| ----------------------------- | ------------------------------- |
| PostgreSQL container          | **RDS** (managed PostgreSQL)    |
| Local files (photos, docs)    | **S3** bucket                   |
| `app` container               | **ECS** (Fargate) or **EC2**    |
| Chroma (embedded)             | **Pinecone** (managed vector DB)|
| Fine-tuned model (local dir)  | **SageMaker** endpoint (optional) or bundled in the image |
| Claude API                    | Anthropic API, or **Bedrock**   |

## Steps (high level)

1. **Build & push the image** to Amazon ECR:
   - `docker build -t insurclaim -f infra/Dockerfile .`
   - tag and push to your ECR repository.
2. **Database:** create an RDS PostgreSQL instance; apply `insurclaim/db/schema.sql`
   once; put the connection details in the task's environment variables.
3. **Storage:** create an S3 bucket for claim documents and photos.
4. **Secrets:** store `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, and the
   database password in **AWS Secrets Manager** (never bake them into the image).
5. **Run:** create an ECS Fargate service (or an EC2 instance) that runs the image
   with those environment variables and secrets.
6. **Vector DB (optional swap):** replace the Chroma implementation in
   `insurclaim/vectordb/store.py` with a Pinecone implementation; the calling code
   does not change because both share the same `VectorStore` interface.
7. **Model hosting (optional):** host the fine-tuned classifier on a SageMaker
   endpoint, or keep it inside the image for simplicity.

## Security reminders

- No real customer data - this is a synthetic-data portfolio project.
- Keep every key in Secrets Manager or environment variables, never in git.
- Give the ECS task role least-privilege access to only the S3 bucket and secrets
  it needs.
