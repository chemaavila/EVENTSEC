# Vercel deployment (frontend)

## Project settings

**Root Directory**
- `frontend`

**Install Command**
```
npm ci
```

**Build Command**
```
npm run build
```

**Output Directory**
- `dist`

## Environment variables

Required:
- `VITE_API_BASE_URL` (Render backend public URL)
- `VITE_CTI_USE_MOCK` (set to `true` until a CTI API is available)

Optional:
- `VITE_THREATMAP_WS_URL`
- `VITE_EMAIL_PROTECT_BASE_URL`
