import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Check if we are already on the login page to avoid loops
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                // Optional: Dispatch a custom event so UI can show a toast before redirecting
                window.dispatchEvent(new Event('session-expired'));

                // Redirect to login
                // window.location.href = '/login'; // Uncomment to auto-redirect
            }
        }
        return Promise.reject(error);
    }
);

export default api;
