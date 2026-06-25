const api = require("../../utils/api");

function asParts(parts) {
  if (!Array.isArray(parts)) return [];
  return parts.map((item, index) => ({
    name: item.name || `部件${index + 1}`,
    length_mm: item.length_mm || "",
    width_mm: item.width_mm || "",
    quantity: item.quantity || 1,
    material_category: item.material_category || "",
    material_name: item.material_name || "",
    process_name: item.process_name || "",
    matched_category_id: item.matched_category_id || null,
    matched_material_id: item.matched_material_id || null,
    matched_process_id: item.matched_process_id || null,
    notes: item.notes || "",
    confidence: item.confidence || 0
  }));
}

Page({
  data: {
    imagePath: "",
    hint: "",
    recognizing: false,
    result: null,
    parts: [],
    warnings: []
  },

  onHintInput(event) {
    this.setData({ hint: event.detail.value });
  },

  chooseImage() {
    if (wx.chooseMedia) {
      wx.chooseMedia({
        count: 1,
        mediaType: ["image"],
        sourceType: ["album", "camera"],
        sizeType: ["compressed"],
        success: (res) => {
          const file = res.tempFiles && res.tempFiles[0];
          this.setData({
            imagePath: file ? file.tempFilePath : "",
            result: null,
            parts: [],
            warnings: []
          });
        }
      });
      return;
    }

    wx.chooseImage({
      count: 1,
      sourceType: ["album", "camera"],
      sizeType: ["compressed"],
      success: (res) => {
        this.setData({
          imagePath: res.tempFilePaths[0] || "",
          result: null,
          parts: [],
          warnings: []
        });
      }
    });
  },

  previewImage() {
    if (!this.data.imagePath) return;
    wx.previewImage({ urls: [this.data.imagePath] });
  },

  async recognizeImage() {
    if (!this.data.imagePath) {
      wx.showToast({ title: "请先上传图片", icon: "none" });
      return;
    }

    this.setData({ recognizing: true });
    wx.showLoading({ title: "识别中" });
    try {
      const result = await api.uploadImage("/api/vision/recognize", this.data.imagePath, {
        hint: this.data.hint || ""
      });

      const parts = asParts(result.parts);
      this.setData({
        recognizing: false,
        result,
        parts,
        warnings: result.warnings || []
      });

      if (!result.configured) {
        wx.showModal({
          title: "当前为演示模式",
          content: "服务器还没有接入真实 AI，页面流程可测试，实际识别需配置 OpenClaw 或 OpenAI。",
          showCancel: false
        });
      } else if (!parts.length) {
        wx.showToast({ title: "未识别到部件", icon: "none" });
      } else {
        wx.showToast({ title: "识别完成", icon: "success" });
      }
    } catch (error) {
      this.setData({ recognizing: false });
      wx.showModal({
        title: "识别失败",
        content: error.message || "请稍后重试",
        showCancel: false
      });
    } finally {
      wx.hideLoading();
    }
  },

  onPartInput(event) {
    const index = Number(event.currentTarget.dataset.index);
    const field = event.currentTarget.dataset.field;
    const value = event.detail.value;
    this.setData({ [`parts[${index}].${field}`]: value });
  },

  applyToQuote() {
    if (!this.data.parts.length) {
      wx.showToast({ title: "没有可带入的部件", icon: "none" });
      return;
    }

    wx.setStorageSync("recognizedPartsForQuote", {
      image_type: this.data.result ? this.data.result.image_type : "",
      parts: this.data.parts,
      created_at: Date.now()
    });

    wx.switchTab({ url: "/pages/quote/quote" });
  },

  clearAll() {
    this.setData({
      imagePath: "",
      hint: "",
      result: null,
      parts: [],
      warnings: []
    });
  }
});
