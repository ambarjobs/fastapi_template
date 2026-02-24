-- CREATE TABLE address (
-- 	id INTEGER GENERATED ALWAYS AS IDENTITY (INCREMENT BY 1 START WITH 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 NO CYCLE),
-- 	street VARCHAR(255) NOT NULL,
-- 	district VARCHAR,
-- 	city VARCHAR(255) NOT NULL,
-- 	state VARCHAR(2) NOT NULL,
-- 	country VARCHAR(2) NOT NULL,
-- 	zip_code VARCHAR(9) NOT NULL,
-- 	CONSTRAINT address_pkey PRIMARY KEY (id)
-- );


-- CREATE TABLE role (
-- 	id INTEGER GENERATED ALWAYS AS IDENTITY (INCREMENT BY 1 START WITH 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 NO CYCLE),
-- 	name VARCHAR(255) NOT NULL,
-- 	CONSTRAINT role_pkey PRIMARY KEY (id),
-- 	CONSTRAINT role_name_key UNIQUE NULLS DISTINCT (name),
-- 	CONSTRAINT role_name_check CHECK (name::text = ANY (ARRAY['guest'::character varying, 'user'::character varying, 'admin'::character varying]::text[]))
-- );


-- CREATE TABLE "user" (
-- 	id INTEGER GENERATED ALWAYS AS IDENTITY (INCREMENT BY 1 START WITH 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 NO CYCLE),
-- 	email VARCHAR(255) NOT NULL,
-- 	first_name VARCHAR(255) NOT NULL,
-- 	last_name VARCHAR,
-- 	password_hash VARCHAR(255) NOT NULL,
-- 	address_id INTEGER,
-- 	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
-- 	CONSTRAINT user_pkey PRIMARY KEY (id),
-- 	CONSTRAINT user_address_id_fkey FOREIGN KEY(address_id) REFERENCES address (id),
-- 	CONSTRAINT user_email_key UNIQUE NULLS DISTINCT (email)
-- );


-- CREATE TABLE user_role (
-- 	user_id INTEGER NOT NULL,
-- 	role_id INTEGER NOT NULL,
-- 	CONSTRAINT user_role_pkey PRIMARY KEY (user_id, role_id),
-- 	CONSTRAINT user_role_role_id_fkey FOREIGN KEY(role_id) REFERENCES role (id),
-- 	CONSTRAINT user_role_user_id_fkey FOREIGN KEY(user_id) REFERENCES "user" (id)
-- );


-- INSERT INTO role (name) VALUES ('guest'), ('user'), ('admin') ON CONFLICT (name) DO NOTHING;
