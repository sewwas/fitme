// ==============================================================================
// Fit Me Fitness Club — Portal & Backend URL Configuration
// ==============================================================================

/**
 * Base URL for the Django backend / member portal.
 * Defaults to the production Render service if not provided in environment.
 */
export const PORTAL_BASE_URL: string = (
  process.env.NEXT_PUBLIC_API_URL || "https://fitme-backend-mucu.onrender.com"
).replace(/\/$/, "");

/**
 * Direct link to Member / Staff Login page
 */
export const PORTAL_LOGIN_URL: string = `${PORTAL_BASE_URL}/login/`;

/**
 * Direct link to Member Registration page
 */
export const PORTAL_REGISTER_URL: string = `${PORTAL_BASE_URL}/register/`;
