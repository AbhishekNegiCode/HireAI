--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: audit_application_status(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.audit_application_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
      IF TG_OP = 'INSERT' THEN
        INSERT INTO application_status_history(application_id, old_status, new_status, changed_by)
        VALUES (NEW.application_id, NULL, NEW.status, NULLIF(current_setting('app.user_id', true), '')::integer);
      ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO application_status_history(application_id, old_status, new_status, changed_by)
        VALUES (NEW.application_id, OLD.status, NEW.status, NULLIF(current_setting('app.user_id', true), '')::integer);
        UPDATE applications SET updated_at = CURRENT_TIMESTAMP WHERE application_id = NEW.application_id;
      END IF;
      RETURN NEW;
    END;
    $$;


--
-- Name: required_skill_match(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.required_skill_match(candidate integer, target_job integer) RETURNS numeric
    LANGUAGE sql STABLE
    AS $$
 SELECT CASE WHEN COUNT(*) = 0 THEN 100
 ELSE 100.0 * COUNT(cs.skill_id) / COUNT(*) END
 FROM job_skills js LEFT JOIN candidate_skills cs
 ON cs.skill_id = js.skill_id AND cs.candidate_id = candidate
 WHERE js.job_id = target_job AND js.is_required;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: application_status_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_status_history (
    history_id integer NOT NULL,
    application_id integer NOT NULL,
    old_status character varying(30),
    new_status character varying(30) NOT NULL,
    changed_by integer,
    changed_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: application_status_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.application_status_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: application_status_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.application_status_history_history_id_seq OWNED BY public.application_status_history.history_id;


--
-- Name: applications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.applications (
    application_id integer NOT NULL,
    candidate_id integer NOT NULL,
    job_id integer NOT NULL,
    resume_id integer NOT NULL,
    cover_letter text NOT NULL,
    status character varying(30) NOT NULL,
    applied_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT applications_status_check CHECK (((status)::text = ANY ((ARRAY['Applied'::character varying, 'Under Review'::character varying, 'Shortlisted'::character varying, 'Interview Scheduled'::character varying, 'Selected'::character varying, 'Rejected'::character varying, 'Withdrawn'::character varying])::text[])))
);


--
-- Name: applications_application_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.applications_application_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: applications_application_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.applications_application_id_seq OWNED BY public.applications.application_id;


--
-- Name: auth_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_sessions (
    session_id character varying(64) NOT NULL,
    user_id integer NOT NULL,
    csrf character varying(64) NOT NULL,
    expires_at timestamp without time zone NOT NULL
);


--
-- Name: candidate_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.candidate_profiles (
    candidate_id integer NOT NULL,
    user_id integer NOT NULL,
    phone character varying(40) NOT NULL,
    location character varying(160) NOT NULL,
    headline character varying(200) NOT NULL,
    professional_summary text NOT NULL,
    total_experience double precision NOT NULL,
    portfolio_url character varying(500) NOT NULL,
    linkedin_url character varying(500) NOT NULL,
    github_url character varying(500) NOT NULL,
    CONSTRAINT candidate_profiles_total_experience_check CHECK (((total_experience >= (0)::double precision) AND (total_experience <= (80)::double precision)))
);


--
-- Name: candidate_profiles_candidate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.candidate_profiles_candidate_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: candidate_profiles_candidate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.candidate_profiles_candidate_id_seq OWNED BY public.candidate_profiles.candidate_id;


--
-- Name: candidate_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.candidate_skills (
    candidate_id integer NOT NULL,
    skill_id integer NOT NULL,
    proficiency_level character varying(20) NOT NULL,
    years_of_experience double precision NOT NULL,
    CONSTRAINT candidate_skills_years_of_experience_check CHECK ((years_of_experience >= (0)::double precision))
);


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    company_id integer NOT NULL,
    company_name character varying(160) NOT NULL,
    description text NOT NULL,
    website character varying(500) NOT NULL,
    industry character varying(100) NOT NULL,
    company_size character varying(50) NOT NULL,
    location character varying(160) NOT NULL,
    logo_url character varying(500) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: companies_company_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.companies_company_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: companies_company_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_company_id_seq OWNED BY public.companies.company_id;


--
-- Name: education; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.education (
    education_id integer NOT NULL,
    candidate_id integer NOT NULL,
    institution character varying(200) NOT NULL,
    degree character varying(200) NOT NULL,
    start_year integer NOT NULL,
    end_year integer,
    CONSTRAINT education_check CHECK (((end_year IS NULL) OR (end_year >= start_year)))
);


--
-- Name: education_education_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.education_education_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: education_education_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.education_education_id_seq OWNED BY public.education.education_id;


--
-- Name: experience; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.experience (
    experience_id integer NOT NULL,
    candidate_id integer NOT NULL,
    company character varying(200) NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    start_date date NOT NULL,
    end_date date,
    CONSTRAINT experience_check CHECK (((end_date IS NULL) OR (end_date >= start_date)))
);


--
-- Name: experience_experience_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experience_experience_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experience_experience_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.experience_experience_id_seq OWNED BY public.experience.experience_id;


--
-- Name: job_application_counts; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.job_application_counts AS
SELECT
    NULL::integer AS job_id,
    NULL::character varying(200) AS title,
    NULL::integer AS recruiter_id,
    NULL::bigint AS applicant_count,
    NULL::bigint AS shortlisted_count;


--
-- Name: job_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.job_embeddings (
    embedding_id integer NOT NULL,
    job_id integer NOT NULL,
    embedding public.vector(384) NOT NULL,
    model_name character varying(100) NOT NULL
);


--
-- Name: job_embeddings_embedding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.job_embeddings_embedding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: job_embeddings_embedding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.job_embeddings_embedding_id_seq OWNED BY public.job_embeddings.embedding_id;


--
-- Name: job_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.job_recommendations (
    recommendation_id integer NOT NULL,
    candidate_id integer NOT NULL,
    job_id integer NOT NULL,
    skill_match_score double precision NOT NULL,
    semantic_match_score double precision,
    experience_score double precision NOT NULL,
    location_score double precision NOT NULL,
    overall_score double precision NOT NULL,
    explanation jsonb NOT NULL,
    generated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT job_recommendations_overall_score_check CHECK (((overall_score >= (0)::double precision) AND (overall_score <= (100)::double precision)))
);


--
-- Name: job_recommendations_recommendation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.job_recommendations_recommendation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: job_recommendations_recommendation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.job_recommendations_recommendation_id_seq OWNED BY public.job_recommendations.recommendation_id;


--
-- Name: job_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.job_skills (
    job_id integer NOT NULL,
    skill_id integer NOT NULL,
    importance integer NOT NULL,
    is_required boolean NOT NULL,
    CONSTRAINT job_skills_importance_check CHECK (((importance >= 1) AND (importance <= 5)))
);


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.jobs (
    job_id integer NOT NULL,
    company_id integer NOT NULL,
    recruiter_id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    responsibilities text NOT NULL,
    employment_type character varying(40) NOT NULL,
    experience_min double precision NOT NULL,
    experience_max double precision NOT NULL,
    salary_min integer NOT NULL,
    salary_max integer NOT NULL,
    location character varying(160) NOT NULL,
    work_mode character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    posted_at timestamp without time zone DEFAULT now() NOT NULL,
    application_deadline date,
    embedding_status character varying(30) NOT NULL,
    CONSTRAINT jobs_check CHECK (((experience_min >= (0)::double precision) AND (experience_max >= experience_min))),
    CONSTRAINT jobs_check1 CHECK (((salary_min >= 0) AND (salary_max >= salary_min))),
    CONSTRAINT jobs_employment_type_check CHECK (((employment_type)::text = ANY ((ARRAY['Full-time'::character varying, 'Part-time'::character varying, 'Contract'::character varying, 'Internship'::character varying])::text[]))),
    CONSTRAINT jobs_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'closed'::character varying, 'draft'::character varying])::text[]))),
    CONSTRAINT jobs_work_mode_check CHECK (((work_mode)::text = ANY ((ARRAY['Remote'::character varying, 'Hybrid'::character varying, 'On-site'::character varying])::text[])))
);


--
-- Name: jobs_job_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.jobs_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: jobs_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.jobs_job_id_seq OWNED BY public.jobs.job_id;


--
-- Name: recruiter_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recruiter_profiles (
    recruiter_id integer NOT NULL,
    user_id integer NOT NULL,
    company_id integer,
    designation character varying(120) NOT NULL
);


--
-- Name: recruiter_profiles_recruiter_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recruiter_profiles_recruiter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recruiter_profiles_recruiter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recruiter_profiles_recruiter_id_seq OWNED BY public.recruiter_profiles.recruiter_id;


--
-- Name: reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reports (
    report_id integer NOT NULL,
    user_id integer NOT NULL,
    job_id integer NOT NULL,
    reason text NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT reports_status_check CHECK (((status)::text = ANY ((ARRAY['open'::character varying, 'resolved'::character varying, 'dismissed'::character varying])::text[])))
);


--
-- Name: reports_report_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reports_report_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reports_report_id_seq OWNED BY public.reports.report_id;


--
-- Name: resume_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resume_analyses (
    analysis_id integer NOT NULL,
    resume_id integer NOT NULL,
    education jsonb NOT NULL,
    experience_years double precision NOT NULL,
    professional_summary text NOT NULL,
    extracted_projects jsonb NOT NULL,
    suggested_roles jsonb NOT NULL,
    analysis_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: resume_analyses_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resume_analyses_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resume_analyses_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resume_analyses_analysis_id_seq OWNED BY public.resume_analyses.analysis_id;


--
-- Name: resume_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resume_embeddings (
    embedding_id integer NOT NULL,
    resume_id integer NOT NULL,
    embedding public.vector(384) NOT NULL,
    model_name character varying(100) NOT NULL
);


--
-- Name: resume_embeddings_embedding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resume_embeddings_embedding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resume_embeddings_embedding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resume_embeddings_embedding_id_seq OWNED BY public.resume_embeddings.embedding_id;


--
-- Name: resumes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resumes (
    resume_id integer NOT NULL,
    candidate_id integer NOT NULL,
    original_filename character varying(255) NOT NULL,
    storage_path character varying(500) NOT NULL,
    extracted_text text NOT NULL,
    is_active boolean NOT NULL,
    uploaded_at timestamp without time zone DEFAULT now() NOT NULL,
    analysis_status character varying(30) NOT NULL,
    analysis_error text NOT NULL
);


--
-- Name: resumes_resume_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resumes_resume_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resumes_resume_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resumes_resume_id_seq OWNED BY public.resumes.resume_id;


--
-- Name: saved_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saved_jobs (
    saved_job_id integer NOT NULL,
    candidate_id integer NOT NULL,
    job_id integer NOT NULL,
    saved_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: saved_jobs_saved_job_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.saved_jobs_saved_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: saved_jobs_saved_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.saved_jobs_saved_job_id_seq OWNED BY public.saved_jobs.saved_job_id;


--
-- Name: skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skills (
    skill_id integer NOT NULL,
    skill_name character varying(100) NOT NULL,
    normalized_skill_name character varying(100) NOT NULL
);


--
-- Name: skills_skill_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.skills_skill_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: skills_skill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.skills_skill_id_seq OWNED BY public.skills.skill_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    full_name character varying(120) NOT NULL,
    email character varying(254) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['candidate'::character varying, 'recruiter'::character varying, 'admin'::character varying])::text[])))
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: application_status_history history_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_status_history ALTER COLUMN history_id SET DEFAULT nextval('public.application_status_history_history_id_seq'::regclass);


--
-- Name: applications application_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications ALTER COLUMN application_id SET DEFAULT nextval('public.applications_application_id_seq'::regclass);


--
-- Name: candidate_profiles candidate_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_profiles ALTER COLUMN candidate_id SET DEFAULT nextval('public.candidate_profiles_candidate_id_seq'::regclass);


--
-- Name: companies company_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN company_id SET DEFAULT nextval('public.companies_company_id_seq'::regclass);


--
-- Name: education education_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.education ALTER COLUMN education_id SET DEFAULT nextval('public.education_education_id_seq'::regclass);


--
-- Name: experience experience_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experience ALTER COLUMN experience_id SET DEFAULT nextval('public.experience_experience_id_seq'::regclass);


--
-- Name: job_embeddings embedding_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_embeddings ALTER COLUMN embedding_id SET DEFAULT nextval('public.job_embeddings_embedding_id_seq'::regclass);


--
-- Name: job_recommendations recommendation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_recommendations ALTER COLUMN recommendation_id SET DEFAULT nextval('public.job_recommendations_recommendation_id_seq'::regclass);


--
-- Name: jobs job_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs ALTER COLUMN job_id SET DEFAULT nextval('public.jobs_job_id_seq'::regclass);


--
-- Name: recruiter_profiles recruiter_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recruiter_profiles ALTER COLUMN recruiter_id SET DEFAULT nextval('public.recruiter_profiles_recruiter_id_seq'::regclass);


--
-- Name: reports report_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports ALTER COLUMN report_id SET DEFAULT nextval('public.reports_report_id_seq'::regclass);


--
-- Name: resume_analyses analysis_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_analyses ALTER COLUMN analysis_id SET DEFAULT nextval('public.resume_analyses_analysis_id_seq'::regclass);


--
-- Name: resume_embeddings embedding_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_embeddings ALTER COLUMN embedding_id SET DEFAULT nextval('public.resume_embeddings_embedding_id_seq'::regclass);


--
-- Name: resumes resume_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes ALTER COLUMN resume_id SET DEFAULT nextval('public.resumes_resume_id_seq'::regclass);


--
-- Name: saved_jobs saved_job_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_jobs ALTER COLUMN saved_job_id SET DEFAULT nextval('public.saved_jobs_saved_job_id_seq'::regclass);


--
-- Name: skills skill_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills ALTER COLUMN skill_id SET DEFAULT nextval('public.skills_skill_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: application_status_history application_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_status_history
    ADD CONSTRAINT application_status_history_pkey PRIMARY KEY (history_id);


--
-- Name: applications applications_candidate_id_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_candidate_id_job_id_key UNIQUE (candidate_id, job_id);


--
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (application_id);


--
-- Name: auth_sessions auth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: candidate_profiles candidate_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_profiles
    ADD CONSTRAINT candidate_profiles_pkey PRIMARY KEY (candidate_id);


--
-- Name: candidate_profiles candidate_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_profiles
    ADD CONSTRAINT candidate_profiles_user_id_key UNIQUE (user_id);


--
-- Name: candidate_skills candidate_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_skills
    ADD CONSTRAINT candidate_skills_pkey PRIMARY KEY (candidate_id, skill_id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (company_id);


--
-- Name: education education_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.education
    ADD CONSTRAINT education_pkey PRIMARY KEY (education_id);


--
-- Name: experience experience_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experience
    ADD CONSTRAINT experience_pkey PRIMARY KEY (experience_id);


--
-- Name: job_embeddings job_embeddings_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_embeddings
    ADD CONSTRAINT job_embeddings_job_id_key UNIQUE (job_id);


--
-- Name: job_embeddings job_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_embeddings
    ADD CONSTRAINT job_embeddings_pkey PRIMARY KEY (embedding_id);


--
-- Name: job_recommendations job_recommendations_candidate_id_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_recommendations
    ADD CONSTRAINT job_recommendations_candidate_id_job_id_key UNIQUE (candidate_id, job_id);


--
-- Name: job_recommendations job_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_recommendations
    ADD CONSTRAINT job_recommendations_pkey PRIMARY KEY (recommendation_id);


--
-- Name: job_skills job_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_skills
    ADD CONSTRAINT job_skills_pkey PRIMARY KEY (job_id, skill_id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (job_id);


--
-- Name: recruiter_profiles recruiter_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recruiter_profiles
    ADD CONSTRAINT recruiter_profiles_pkey PRIMARY KEY (recruiter_id);


--
-- Name: recruiter_profiles recruiter_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recruiter_profiles
    ADD CONSTRAINT recruiter_profiles_user_id_key UNIQUE (user_id);


--
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (report_id);


--
-- Name: resume_analyses resume_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_analyses
    ADD CONSTRAINT resume_analyses_pkey PRIMARY KEY (analysis_id);


--
-- Name: resume_analyses resume_analyses_resume_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_analyses
    ADD CONSTRAINT resume_analyses_resume_id_key UNIQUE (resume_id);


--
-- Name: resume_embeddings resume_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_embeddings
    ADD CONSTRAINT resume_embeddings_pkey PRIMARY KEY (embedding_id);


--
-- Name: resume_embeddings resume_embeddings_resume_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_embeddings
    ADD CONSTRAINT resume_embeddings_resume_id_key UNIQUE (resume_id);


--
-- Name: resumes resumes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_pkey PRIMARY KEY (resume_id);


--
-- Name: saved_jobs saved_jobs_candidate_id_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_jobs
    ADD CONSTRAINT saved_jobs_candidate_id_job_id_key UNIQUE (candidate_id, job_id);


--
-- Name: saved_jobs saved_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_jobs
    ADD CONSTRAINT saved_jobs_pkey PRIMARY KEY (saved_job_id);


--
-- Name: skills skills_normalized_skill_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_normalized_skill_name_key UNIQUE (normalized_skill_name);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (skill_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_application_status_history_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_application_status_history_application_id ON public.application_status_history USING btree (application_id);


--
-- Name: ix_application_status_history_changed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_application_status_history_changed_by ON public.application_status_history USING btree (changed_by);


--
-- Name: ix_applications_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_candidate_id ON public.applications USING btree (candidate_id);


--
-- Name: ix_applications_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_job_id ON public.applications USING btree (job_id);


--
-- Name: ix_applications_resume_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_resume_id ON public.applications USING btree (resume_id);


--
-- Name: ix_applications_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_status ON public.applications USING btree (status);


--
-- Name: ix_auth_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_auth_sessions_user_id ON public.auth_sessions USING btree (user_id);


--
-- Name: ix_candidate_skills_skill_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_candidate_skills_skill_id ON public.candidate_skills USING btree (skill_id);


--
-- Name: ix_companies_company_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_companies_company_name ON public.companies USING btree (company_name);


--
-- Name: ix_education_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_education_candidate_id ON public.education USING btree (candidate_id);


--
-- Name: ix_experience_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_experience_candidate_id ON public.experience USING btree (candidate_id);


--
-- Name: ix_job_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_embedding_hnsw ON public.job_embeddings USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: ix_job_recommendations_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_recommendations_candidate_id ON public.job_recommendations USING btree (candidate_id);


--
-- Name: ix_job_recommendations_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_recommendations_job_id ON public.job_recommendations USING btree (job_id);


--
-- Name: ix_job_skills_skill_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_skills_skill_id ON public.job_skills USING btree (skill_id);


--
-- Name: ix_jobs_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_company_id ON public.jobs USING btree (company_id);


--
-- Name: ix_jobs_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_location ON public.jobs USING btree (location);


--
-- Name: ix_jobs_posted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_posted_at ON public.jobs USING btree (posted_at);


--
-- Name: ix_jobs_recruiter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_recruiter_id ON public.jobs USING btree (recruiter_id);


--
-- Name: ix_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_status ON public.jobs USING btree (status);


--
-- Name: ix_jobs_title; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_title ON public.jobs USING btree (title);


--
-- Name: ix_recruiter_profiles_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recruiter_profiles_company_id ON public.recruiter_profiles USING btree (company_id);


--
-- Name: ix_reports_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_job_id ON public.reports USING btree (job_id);


--
-- Name: ix_reports_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_user_id ON public.reports USING btree (user_id);


--
-- Name: ix_resumes_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resumes_candidate_id ON public.resumes USING btree (candidate_id);


--
-- Name: ix_saved_jobs_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_saved_jobs_candidate_id ON public.saved_jobs USING btree (candidate_id);


--
-- Name: ix_saved_jobs_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_saved_jobs_job_id ON public.saved_jobs USING btree (job_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: uq_active_resume; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_active_resume ON public.resumes USING btree (candidate_id) WHERE (is_active = true);


--
-- Name: job_application_counts _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.job_application_counts AS
 SELECT j.job_id,
    j.title,
    j.recruiter_id,
    count(a.application_id) AS applicant_count,
    count(a.application_id) FILTER (WHERE ((a.status)::text = 'Shortlisted'::text)) AS shortlisted_count
   FROM (public.jobs j
     LEFT JOIN public.applications a ON ((a.job_id = j.job_id)))
  GROUP BY j.job_id;


--
-- Name: applications application_status_audit; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER application_status_audit AFTER INSERT OR UPDATE OF status ON public.applications FOR EACH ROW EXECUTE FUNCTION public.audit_application_status();


--
-- Name: application_status_history application_status_history_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_status_history
    ADD CONSTRAINT application_status_history_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(application_id) ON DELETE CASCADE;


--
-- Name: application_status_history application_status_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_status_history
    ADD CONSTRAINT application_status_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(user_id);


--
-- Name: applications applications_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id);


--
-- Name: applications applications_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id);


--
-- Name: applications applications_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id);


--
-- Name: auth_sessions auth_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: candidate_profiles candidate_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_profiles
    ADD CONSTRAINT candidate_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: candidate_skills candidate_skills_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_skills
    ADD CONSTRAINT candidate_skills_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id) ON DELETE CASCADE;


--
-- Name: candidate_skills candidate_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidate_skills
    ADD CONSTRAINT candidate_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(skill_id);


--
-- Name: education education_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.education
    ADD CONSTRAINT education_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id) ON DELETE CASCADE;


--
-- Name: experience experience_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experience
    ADD CONSTRAINT experience_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id) ON DELETE CASCADE;


--
-- Name: job_embeddings job_embeddings_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_embeddings
    ADD CONSTRAINT job_embeddings_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_recommendations job_recommendations_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_recommendations
    ADD CONSTRAINT job_recommendations_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id) ON DELETE CASCADE;


--
-- Name: job_recommendations job_recommendations_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_recommendations
    ADD CONSTRAINT job_recommendations_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_skills job_skills_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_skills
    ADD CONSTRAINT job_skills_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_skills job_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_skills
    ADD CONSTRAINT job_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(skill_id);


--
-- Name: jobs jobs_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(company_id);


--
-- Name: jobs jobs_recruiter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_recruiter_id_fkey FOREIGN KEY (recruiter_id) REFERENCES public.recruiter_profiles(recruiter_id);


--
-- Name: recruiter_profiles recruiter_profiles_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recruiter_profiles
    ADD CONSTRAINT recruiter_profiles_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(company_id);


--
-- Name: recruiter_profiles recruiter_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recruiter_profiles
    ADD CONSTRAINT recruiter_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: reports reports_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- Name: reports reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: resume_analyses resume_analyses_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_analyses
    ADD CONSTRAINT resume_analyses_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE;


--
-- Name: resume_embeddings resume_embeddings_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_embeddings
    ADD CONSTRAINT resume_embeddings_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE;


--
-- Name: resumes resumes_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id) ON DELETE CASCADE;


--
-- Name: saved_jobs saved_jobs_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_jobs
    ADD CONSTRAINT saved_jobs_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES public.candidate_profiles(candidate_id) ON DELETE CASCADE;


--
-- Name: saved_jobs saved_jobs_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_jobs
    ADD CONSTRAINT saved_jobs_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

