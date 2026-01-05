# Contribución

## Flujo de trabajo
1. Crea un branch desde `main`:
   ```bash
   git checkout -b feat/mi-cambio
   ```
2. Realiza cambios con commits pequeños y descriptivos.
3. Abre PR con contexto, pruebas y capturas si aplica.

## Estilo de commits
- Prefijos recomendados: `feat:`, `fix:`, `docs:`, `chore:`.

## Tests
### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```

## Checklist PR
- [ ] Documentación actualizada si cambia comportamiento.
- [ ] Tests ejecutados (o justificación).
- [ ] Sin secretos en el repo.
