# RESTAURANT API
so this is a really cool API for restaurants using django and a few other things, works really well

> Setup
1. Clone the repo and open the folder
2. Create and activate a virtual environment:
   `python -m venv venv` then `venv\Scripts\activate` (windows only idk what mac is)
3. Install dependencies: `pip install -r requirements.txt`
4. Create the database tables: `python manage.py migrate`
5. Create a staff user: `python manage.py createsuperuser`
6. Start the server: `python manage.py runserver`
7. Open `http://127.0.0.1:8000/api/`

# Users + authentication

- *Staff* users have `is_staff` enabled. The superuser from step 5 is staff so superuser = admin = staff
- *Customers* are regular people Create them in the admin panel at
  `/admin/` (leave "Staff status" unticked).
- Get a token by POSTing a username and password to `/api/token/`, then send it
  in the `Authorization: Token <your-token>` header.

> Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | /api/menu/ | None | List menu items (filter with `?category=`) |
| GET | /api/menu/{id}/ | None | Retrieve a menu item |
| POST | /api/menu/ | Staff | Create a menu item |
| PATCH | /api/menu/{id}/ | Staff | Update a menu item |
| DELETE | /api/menu/{id}/ | Staff | Remove a menu item |
| POST | /api/orders/ | Customer | Place an order |
| GET | /api/orders/ | Staff | List orders (filter with `?status=`) |
| GET | /api/orders/{id}/ | Staff or owner | Retrieve an order |
| PATCH | /api/orders/{id}/ | Staff | Update order status |

all list endpoints are paginated

> some examples

- Get a token
curl command and the JSON response

- GET /api/menu/?category=appetizers
curl command and the JSON response

- POST /api/menu/ (staff)
curl command and the JSON response, plus the 403 a customer gets

- POST /api/orders/ (customer)
curl command and the JSON response, plus the 400 for a sold-out item

- PATCH /api/orders/{id}/ (staff)
a valid move, plus the 400 for an invalid one


  67
# 67
> 67
` 67 `
- 67

have fun