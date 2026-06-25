const API_BASE = "https://posm.mingbang.net/quote";

function request(path, options = {}) {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method: options.method || "GET",
      data: options.data || {},
      header: {
        "Content-Type": "application/json",
        ...(options.header || {})
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }

        reject(new Error(`请求失败 ${res.statusCode}`));
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

function uploadImage(path, filePath, formData = {}) {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url,
      filePath,
      name: "image",
      formData,
      success(res) {
        let data = {};
        try {
          data = JSON.parse(res.data || "{}");
        } catch (error) {
          reject(new Error("识别服务返回格式错误"));
          return;
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
          return;
        }

        reject(new Error(data.message || `请求失败 ${res.statusCode}`));
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

module.exports = {
  API_BASE,
  request,
  uploadImage
};
