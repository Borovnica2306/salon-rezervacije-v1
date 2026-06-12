import localforage from "localforage";

const store = localforage.createInstance({
  name: "beauty_booking",
  storeName: "auth",
});

const TOKEN_KEY = "access_token";

// In-memory mirror for synchronous reads
let _token = null;

/** Called once at app startup before rendering */
export const initAuthStorage = async () => {
  try {
    _token = await store.getItem(TOKEN_KEY);
  } catch {
    _token = null;
  }
  // Migrate from legacy localStorage if IndexedDB is empty
  if (!_token) {
    const legacy = localStorage.getItem(TOKEN_KEY);
    if (legacy) {
      _token = legacy;
      await store.setItem(TOKEN_KEY, legacy).catch(() => {});
      localStorage.removeItem(TOKEN_KEY);
    }
  }
  return _token;
};

/** Synchronous read from in-memory cache */
export const getToken = () => _token;

/** Persist token to IndexedDB + update memory */
export const setToken = async (token) => {
  _token = token;
  await store.setItem(TOKEN_KEY, token).catch(() => {});
};

/** Remove token from IndexedDB + clear memory */
export const removeToken = async () => {
  _token = null;
  await store.removeItem(TOKEN_KEY).catch(() => {});
};
