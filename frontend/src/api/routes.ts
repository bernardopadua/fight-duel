const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const ROUTES = {
    login: () => `${API_BASE_URL}/api/auth/login/`,
    register: () => `${API_BASE_URL}/api/auth/register/`,
};

export { ROUTES };