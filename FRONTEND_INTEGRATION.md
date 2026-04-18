# Frontend Integration Guide

## Deployment model

You do **not** need to run a second internal backend service for the generation flow.

The intended architecture is:

1. Your frontend talks only to **this current backend**.
2. This backend talks to **Higgsfield** as an external provider.
3. Higgsfield sends webhook updates back to **this same backend**.

So from the frontend point of view, everything is under the **same backend base URL**.

Example:

- Frontend base API URL: `https://subpeltately-superstoical-shavonne.ngrok-free.dev`
- Generate preview: `https://subpeltately-superstoical-shavonne.ngrok-free.dev/hairstyle-previews`
- Upload photos: `https://subpeltately-superstoical-shavonne.ngrok-free.dev/clients/{client_id}/photos`
- Higgsfield webhook target:
  `https://subpeltately-superstoical-shavonne.ngrok-free.dev/hairstyle-previews/webhooks/higgsfield-image`

## Important environment variables

The backend needs these variables configured:

- `HF_API_KEY`
- `HF_SECRET_KEY`
- `PUBLIC_BASE_URL`
- `CORS_ALLOWED_ORIGINS`

`PUBLIC_BASE_URL` must be the public URL of this backend, for example:

```env
PUBLIC_BASE_URL=https://subpeltately-superstoical-shavonne.ngrok-free.dev
```

`PUBLIC_BASE_URL` is recommended so Higgsfield can push webhook updates to this backend. If it is missing, frontend polling can still reconcile with Higgsfield through the stored `status_url`, but webhook-driven updates will not work.

For local frontend development, allow the frontend origin in CORS:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

If you later deploy the frontend separately, add its production origin too as a comma-separated list.

## Current frontend flow

### 1. Create a client

Endpoint:

`POST /clients/create`

Request body:

```json
{
  "brand": "User",
  "model": "Profile",
  "year": 2026
}
```

Notes:

- This endpoint is still using the old `brand/model/year` schema shape from the existing project.
- For now, the frontend can send placeholder values if needed.
- The response contains `id`, which should be used as `client_id`.

Example response:

```json
{
  "id": 1,
  "brand": "User",
  "model": "Profile",
  "year": 2026
}
```

### 2. Upload client photos

Endpoint:

`POST /clients/{client_id}/photos?photo_type=front`

Supported `photo_type` values:

- `front`
- `rear`
- `left`
- `right`

Request:

- `multipart/form-data`
- field name for file: `file`

Example:

```bash
POST /clients/1/photos?photo_type=front
Content-Type: multipart/form-data
```

Recommended frontend behavior:

- Upload at least one photo before enabling image generation.

### 3. Check photo completeness

Endpoint:

`GET /clients/{client_id}/photos/status`

Example response:

```json
{
  "front": true,
  "rear": true,
  "left": false,
  "right": false,
  "partially_completed": true,
  "complete": false
}
```

Generation currently requires:

- `partially_completed === true`

That means at least one photo is uploaded.

## Hairstyle preview generation API

### 1. Generate preview

Endpoint:

`POST /hairstyle-previews`

Request body:

```json
{
  "client_id": 1,
  "text_prompt": "Modern textured crop with faded sides, natural hairline, realistic studio portrait",
  "aspect_ratio": "1:1",
  "resolution": "720p"
}
```

Example response:

```json
{
  "id": 0,
  "client_id": 1,
  "text_prompt": "Modern textured crop with faded sides, natural hairline, realistic studio portrait",
  "status": "queued",
  "aspect_ratio": "1:1",
  "resolution": "720p",
  "generation_count": 1,
  "provider_request_id": "hf_request_123",
  "status_url": "https://...",
  "cancel_url": "https://...",
  "generated_image_url": null,
  "approved_image_url": null,
  "error": null,
  "created_at": "2026-04-11T12:00:00Z",
  "updated_at": "2026-04-11T12:00:00Z"
}
```

Store:

- `preview.id`

This is the value the frontend should use for polling, approval, regeneration, and cancellation.

### 2. Poll preview status

Endpoint:

`GET /hairstyle-previews/{preview_id}`

Possible status values:

- `queued`
- `processing`
- `completed`
- `failed`
- `blocked`
- `approved`
- `cancelled`

Success condition:

- `status === "completed"`
- `generated_image_url` is not null

Failure condition:

- `status === "failed"` or `status === "blocked"`

Approved condition:

- `status === "approved"`
- `approved_image_url` is not null

### 3. Approve generated hairstyle

Endpoint:

`POST /hairstyle-previews/{preview_id}/approve`

Response:

```json
{
  "ok": true,
  "message": "Preview approved",
  "preview": {
    "id": 0,
    "client_id": 1,
    "text_prompt": "Modern textured crop with faded sides",
    "status": "approved",
    "aspect_ratio": "1:1",
    "resolution": "720p",
    "generation_count": 1,
    "provider_request_id": "hf_request_123",
    "status_url": "https://...",
    "cancel_url": "https://...",
    "generated_image_url": "https://...",
    "approved_image_url": "https://...",
    "error": null,
    "created_at": "2026-04-11T12:00:00Z",
    "updated_at": "2026-04-11T12:01:10Z"
  }
}
```

Use this when the user clicks **Approve**.

### 4. Regenerate preview

Endpoint:

`POST /hairstyle-previews/{preview_id}/regenerate`

Request body:

```json
{
  "text_prompt": "Low taper fade with textured fringe, realistic salon lighting",
  "aspect_ratio": "1:1",
  "resolution": "720p"
}
```

All fields are optional. If omitted, the backend reuses the previous values.

Response:

```json
{
  "ok": true,
  "message": "Preview regeneration started",
  "preview": {
    "...": "same schema as preview response"
  }
}
```

Use this when the user clicks **Regenerate**.

### 5. Cancel preview

Endpoint:

`POST /hairstyle-previews/{preview_id}/cancel`

Response:

```json
{
  "ok": true,
  "message": "Preview cancelled",
  "preview": {
    "...": "same schema as preview response"
  }
}
```

Use this when the user abandons the current generation and wants to start over.

## Recommended frontend state machine

### Draft

- User selects photos
- User enters prompt

### Uploading

- Upload the photos
- Save `client_id`

### Ready to generate

- Enable the generate button when required photos are uploaded

### Generating

1. Call `POST /hairstyle-previews`
2. Save `preview_id`
3. Poll `GET /hairstyle-previews/{preview_id}` every 2-4 seconds

### Generated

When:

- `status === "completed"`
- `generated_image_url` exists

Show:

- generated preview image
- `Approve`
- `Regenerate`
- `Cancel`

### Approved

When:

- user clicks approve
- backend returns `status === "approved"`

Use:

- `approved_image_url`

### Failed or blocked

When:

- `status === "failed"` or `status === "blocked"`

Show:

- error message from `error`
- option to regenerate
- option to cancel

## Example frontend sequence

1. `POST /clients/create`
2. `POST /clients/{client_id}/photos?photo_type=front`
3. `GET /clients/{client_id}/photos/status`
4. `POST /hairstyle-previews`
6. Poll `GET /hairstyle-previews/{preview_id}`
7. If satisfied: `POST /hairstyle-previews/{preview_id}/approve`
8. If not satisfied: `POST /hairstyle-previews/{preview_id}/regenerate`
9. If abandoning: `POST /hairstyle-previews/{preview_id}/cancel`

## Important implementation notes

### 1. Webhook and polling

The preferred completion path is Higgsfield calling:

`POST /hairstyle-previews/webhooks/higgsfield-image`

If webhook delivery is delayed or the backend is not publicly reachable, polling `GET /hairstyle-previews/{preview_id}` will also reconcile the current provider status through Higgsfield's `status_url`.

### 2. Temporary preview storage

Preview jobs are currently stored in memory in the backend.

That means:

- restarting the backend will remove preview job state
- completed jobs are not yet persisted to PostgreSQL

This is acceptable for a temporary integration, but not ideal for production.

### 3. Client model is still legacy

The current `/clients/create` payload still uses:

- `brand`
- `model`
- `year`

This should eventually be refactored to a real barber-domain client schema.

## Suggested frontend TypeScript types

```ts
export type HairstylePreviewStatus =
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "blocked"
  | "approved"
  | "cancelled";

export interface HairstylePreview {
  id: number;
  client_id: number;
  text_prompt: string;
  status: HairstylePreviewStatus;
  aspect_ratio: string;
  resolution: string;
  generation_count: number;
  provider_request_id: string | null;
  status_url: string | null;
  cancel_url: string | null;
  generated_image_url: string | null;
  approved_image_url: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}
```
