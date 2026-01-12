# Login debugging (CORS + proxy)

## Symptoms to watch

- `CORS error` / `Failed to fetch`
- `Access-Control-Allow-Origin` missing
- Preflight `OPTIONS /auth/login` returns `400`
- `login:1 404` (indicates a relative `/login` or mis-built URL)

## Expected behavior

- Preflight returns `200`/`204` with CORS headers.
- `POST /auth/login` returns `200` or a JSON error (`401/422`), **not** blocked by CORS.
- In DevTools, the login request should be `https://<vercel-app>/api/auth/login` (not `onrender.com`).

## cURL checks

### 1) Preflight

```
curl -i -X OPTIONS "https://eventsec-backend.onrender.com/auth/login" \
  -H "Origin: https://eventsec-ihae.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
```

Expected:
- `200` or `204`
- `Access-Control-Allow-Origin: https://eventsec-ihae.vercel.app`
- `Access-Control-Allow-Methods` includes `POST`
- `Access-Control-Allow-Headers` includes `content-type`

### 2) Login POST

```
curl -i -X POST "https://eventsec-backend.onrender.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"1234"}'
```

Expected:
- `200` or `401`/`422` with JSON body
- CORS headers present

### 3) Vercel proxy health

```
curl -i https://eventsec-ihae.vercel.app/api/healthz
```

Expected:
- `200` response via Vercel proxy

## Notes

- `GET /auth/login` should return `405 Method Not Allowed` (the endpoint is **POST** only).
- If you see `login:1 404`, the frontend likely built a relative `/login` URL. Check `VITE_API_URL=/api` and verify the login request URL in DevTools.
