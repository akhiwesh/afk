// API Request Client

/** Turn FastAPI error payloads into a human-readable string. */
function formatApiDetail(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const field = Array.isArray(item.loc)
            ? item.loc.filter((p) => p !== "body").join(" ")
            : "";
          let msg = item.msg || item.message || JSON.stringify(item);
          msg = msg.replace(/^Value error,\s*/i, "");
          return field ? `${field}: ${msg}` : msg;
        }
        return String(item);
      })
      .join(" ");
  }
  if (typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return String(detail);
}

export const API = {
  baseUrl: "/api",

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Auto configure headers
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    // Extract authorization token from local storage if cookie isn't available
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle session expiration
      if (response.status === 401 && endpoint !== "/auth/login") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_profile");
        window.dispatchEvent(new Event("auth-changed"));
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = formatApiDetail(errorData.detail)
          || errorData.message
          || `Request failed with status ${response.status}`;
        throw new Error(message);
      }

      // Check if it's an empty response
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error(`API Error on ${endpoint}:`, error);
      throw error;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  },

  isAuthenticated() {
    return !!localStorage.getItem("access_token");
  },

  getUser() {
    const userJson = localStorage.getItem("user_profile");
    return userJson ? JSON.parse(userJson) : null;
  }
};
