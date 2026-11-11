// Decap 3.17.3 uses this exact key for its Git backend credentials.
// Keep it in this page's memory. Other browser preferences retain normal storage.
(() => {
  const key = 'decap-cms-user';
  const storage = window.localStorage;
  const prototype = Storage.prototype;
  const { getItem, setItem, removeItem } = prototype;
  removeItem.call(storage, key);
  let current = null;
  prototype.getItem = function (name) {
    return this === storage && name === key ? current : getItem.call(this, name);
  };
  prototype.setItem = function (name, value) {
    if (this === storage && name === key) {
      current = String(value);
      return;
    }
    return setItem.call(this, name, value);
  };
  prototype.removeItem = function (name) {
    if (this === storage && name === key) {
      current = null;
      return;
    }
    return removeItem.call(this, name);
  };
})();
