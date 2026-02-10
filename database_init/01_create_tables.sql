-- Tables creation: ------------------------------------------------------------

-- Creating `user` table:
CREATE TABLE public."user" (
	id bigserial NOT NULL,
	email varchar(256) NOT NULL,
	name varchar(256) NOT NULL,
	password_hash varchar(256) NOT NULL,
	address_id bigint,
	CONSTRAINT unique_email UNIQUE (email),
	CONSTRAINT user_pk PRIMARY KEY (id)
);

-- Creating `address` table:
CREATE TABLE public.address (
	id bigserial NOT NULL,
	street varchar(256) NOT NULL,
	district varchar(256),
	city varchar(256) NOT NULL,
	state varchar(4) NOT NULL,
	country varchar(4) NOT NULL,
	CONSTRAINT address_pk PRIMARY KEY (id)
);

-- Creating `role` table:
CREATE TABLE public.role (
	id bigserial NOT NULL,
	name varchar(256) NOT NULL,
	CONSTRAINT unique_name UNIQUE (name),
	CONSTRAINT role_pk PRIMARY KEY (id)
);

-- Creating `user_role` table:
CREATE TABLE public.user_role (
	user_id bigint NOT NULL,
	role_id bigint NOT NULL,
	CONSTRAINT user_role_pk PRIMARY KEY (user_id,role_id)
);


-- Foreign key constraints: ----------------------------------------------------------------

-- Creating `user` table `address_id` foreign key constraint:
ALTER TABLE public."user" ADD CONSTRAINT address_fk FOREIGN KEY (address_id)
REFERENCES public.address (id) MATCH SIMPLE
ON DELETE CASCADE ON UPDATE NO ACTION;

-- Creating `user_role` table `user_id` foreign key constraint:
ALTER TABLE public.user_role ADD CONSTRAINT user_fk FOREIGN KEY (user_id)
REFERENCES public."user" (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;

-- Creating `user_role` table `role_id` foreign key constraint:
ALTER TABLE public.user_role ADD CONSTRAINT role_fk FOREIGN KEY (role_id)
REFERENCES public.role (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
