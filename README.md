The data server component for the export-wins application, a backend providing APIs.

See the corresponding projects export-wins-ui and export-wins-ui-mi and PROJECT_README.md

Note, UI project will need to be rebooted after making changes to models of this project since it gets info on startup from this project

Environment Variables you probably want to set
-----------------------------------------------

(see settings.py for details)

```
UI_SECRET='shared-ui-secret'
ADMIN_SECRET='shared-admin-secret'
MI_SECRET='shared-mi-secret'
DATA_SECRET='shared-data-secret'
DEBUG='1'
DATA_SERVER='localhost:8001'  # port you run this project on, for front-ends
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
SENDING_ADDRESS='noreply@example.com'
FEEDBACK_ADDRESS='feedback@example.com'
```

## Dependencies

### Database
You need a Postgres database to connect to, to run Postgres in a docker container run:

```bash
docker run -d -p 5432:5432 -e POSTGRES_DB=export-wins-data postgres:9
```

Now set your DATABASE_URL to include the default user `postgres`:

```bash
export DATABASE_URL='postgres://postgres@127.0.0.1:5432/export-wins-data'
```
#### Dummy data

Once you have a database you'll need some data.

##### Start with the migrate command to set-up your tables:

```bash
$ ./manage.py migrate
```

This means you have some MI targets and all the wins tables set up but no users or wins

##### Create a user:

```bash
$ ./manage.py create_mi_user --email foo@bar.com
User foo@bar.com created with password: ********
User foo@bar.com added to mi_group
```

##### Create missing HVCs:

```bash
$ ./manage.py create_missing_hvcs
```

##### Create some wins:

the following command will create 1000 confirmed wins across all sectors as the last
user that was added to the system

```bash
$ ./manage.py generate_fake_db 1000
```

This currently only creates wins for FY2015/2016 so you'll need to view that year if
you want to see any data.

## Docker

The image for this should be built by docker hub automatically.

### OSX

Create the required env variables and network alias, then run this:

```bash
docker run -d -p 8000:8000 -e "SECRET_KEY=${SECRET_KEY}" -e "ADMIN_SECRET=${ADMIN_SECRET}" -e "UI_SECRET=${UI_SECRET}" -e "MI_SECRET=${MI_SECRET}" -e "DATABASE_URL=postgres://postgres@10.200.10.1:5432/export-wins-data" -e "EMAIL_HOST=${EMAIL_HOST}" -e "EMAIL_PORT=${EMAIL_PORT}" ukti/export-wins-data:latest
```
