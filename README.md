# salon-navigation-app-backend
Backend for Navisalon web app

## Loyalty Program Endpoints

- `POST /api/loyalty/earn` – award loyalty points for a completed appointment. Accepts `appointmentId` and an optional `points` override. Requires authentication.
- `POST /api/loyalty/redeem` – redeem loyalty points for a discount. Accepts `bid` (business id) and `points`. Only available to authenticated customers.
- `GET /api/clients/view-loyalty-points` – view loyalty balances, program goals, and reward details for each salon.
- `GET /api/owner/loyalty-programs` – list configured loyalty programs for the authenticated owner.
- `PUT /api/owner/loyalty-programs/<lprog_id>` – update thresholds or rewards for an existing loyalty program.
- `DELETE /api/owner/loyalty-programs/<lprog_id>` – remove an existing loyalty program.
