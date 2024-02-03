CREATE TABLE IF NOT EXISTS databasemodel (
    id integer PRIMARY KEY,
    modelversion text  NOT NULL,
    sqlcommand text  NOT NULL,
    executed text NOT NULL,
    UNIQUE (modelversion, sqlcommand)
);
##
INSERT INTO databasemodel (modelversion, sqlcommand, executed) VALUES (20240203, 'create table databasemodel', 'run');
##
CREATE TABLE IF NOT EXISTS projects (
    id integer PRIMARY KEY,
    name text NOT NULL UNIQUE
);
##
INSERT INTO databasemodel (modelversion, sqlcommand, executed) VALUES (20240203, 'create table projects', 'run');
##
CREATE TABLE IF NOT EXISTS timetracking (
    id integer PRIMARY KEY,
    project_id integer,
    project_name text,
    date text NOT NULL,
    calendarweek text NOT NULL,
    month text NOT NULL,
    year text NOT NULL,
    starttimestamp integer NOT NULL,
    starttime text NOT NULL,
    endtimestamp integer NOT NULL,
    endtime text NOT NULL,
    created_on text,
    last_edited_on text,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);
##
INSERT INTO databasemodel (modelversion, sqlcommand, executed) VALUES (20240203, 'create table timetracking', 'run');
