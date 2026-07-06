import { API } from "./api.js";

export class Router {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    
    // Listen for hash changes
    window.addEventListener("hashchange", () => this.handleRoute());
    window.addEventListener("load", () => this.handleRoute());
  }

  addRoute(path, handler, isPrivate = false) {
    this.routes[path] = { handler, isPrivate };
  }

  handleRoute() {
    const hash = window.location.hash || "#";
    
    // Check for exact match or default to dashboard/login depending on auth
    let route = this.routes[hash];
    
    // Handle parameterized routes like #crm/1 or similar
    let param = null;
    if (!route) {
      for (const pattern of Object.keys(this.routes)) {
        if (pattern.includes("/:") && hash.startsWith(pattern.split("/:")[0])) {
          route = this.routes[pattern];
          param = hash.split("/")[1];
          break;
        }
      }
    }

    if (!route) {
      // Fallback
      if (API.isAuthenticated()) {
        window.location.hash = "#dashboard";
      } else {
        window.location.hash = "#";
      }
      return;
    }

    // Auth Protection guard
    if (route.isPrivate && !API.isAuthenticated()) {
      window.location.hash = "#login";
      return;
    }

    // Execute view handler
    this.currentRoute = hash;
    route.handler(param);
  }

  navigate(hash) {
    window.location.hash = hash;
  }
}
export const AppRouter = new Router();
