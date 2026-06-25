const api = require("../../utils/api");
const calculator = require("../../utils/calculator");

function makeId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatMaterialName(item) {
  if (!item) return "";
  return `${item.name}${item.specification ? `（${item.specification}）` : ""}`;
}

function toMoney(value) {
  const amount = Number(value) || 0;
  return amount > 0 ? `¥${amount.toFixed(2)}` : "";
}

function buildRuleLines(payload, result) {
  const areaText = result.area.toFixed(4);
  const materialPrice = Number(payload.material.square_price || 0).toFixed(2);
  const totalQuantity = payload.quantity * payload.projectSets;
  const processLines = Array.isArray(result.details) ? result.details.map((item) => `工艺明细：${item}`) : [];

  return [
    `面积：(长 ${payload.length}+30) × (宽 ${payload.width}+30) ÷ 1000000 = ${areaText} m²`,
    `判定数量：部件数量 ${payload.quantity} × 项目套数 ${payload.projectSets} = ${totalQuantity}`,
    `主材料：${payload.material.name}，平方单价 ¥${materialPrice}，材料单价 ¥${result.materialCost.toFixed(2)}`,
    `工艺标准：${result.standardName || "默认规则"}`,
    ...processLines,
    `单件单价：材料 ¥${result.materialCost.toFixed(2)} + 工艺 ¥${result.processCost.toFixed(2)} = ¥${result.unitPrice.toFixed(2)}`,
    `部件小计：单件 ¥${result.unitPrice.toFixed(2)} × 数量 ${payload.quantity} = ¥${result.totalPrice.toFixed(2)}`
  ];
}

function buildCategoryRows(items, projectSets) {
  const sets = Math.max(Number(projectSets) || 1, 1);
  const mainMaterialTotal = items.reduce((sum, item) => {
    return sum + Number(item.materialCost || 0) * Number(item.quantity || 1);
  }, 0);
  const processingTotal = items.reduce((sum, item) => {
    return sum + Number(item.processCost || 0) * Number(item.quantity || 1);
  }, 0);
  const costTotal = mainMaterialTotal + processingTotal;
  const managementCost = costTotal * 0.07;
  const preTaxTotal = costTotal + managementCost;
  const taxCost = preTaxTotal * 0.17;
  const taxIncludedTotal = preTaxTotal + taxCost;

  const row = (number, name, totalPrice = 0, className = "") => ({
    number,
    name,
    unitPrice: toMoney(totalPrice / sets),
    totalPrice: toMoney(totalPrice),
    className
  });

  return {
    rows: [
      row("01", "主材料", mainMaterialTotal),
      row("02", "画面"),
      row("03", "模具"),
      row("04", "加工费用合计", processingTotal),
      row("05", "配件"),
      row("06", "包装"),
      row("07", "运输"),
      row("08", "人工"),
      row("09", "成本合计（01-08费用合计）", costTotal, "cost-row"),
      row("10", "管理费利润（09*7%）", managementCost),
      row("11", "增值税（10*17%）", taxCost),
      {
        number: "12",
        name: "价格汇总",
        unitLines: [
          `产品不含税单价 ${toMoney(preTaxTotal / sets)}`,
          `产品含税单价 ${toMoney(taxIncludedTotal / sets)}`
        ],
        totalLines: [
          `不含税总价 ${toMoney(preTaxTotal)}`,
          `含税总价 ${toMoney(taxIncludedTotal)}`
        ],
        className: "summary-row",
        isSummary: true
      }
    ],
    taxIncludedTotal
  };
}

Page({
  data: {
    loading: true,
    categories: [],
    materials: [],
    processes: [],
    categoryNames: [],
    processNames: [],
    projectSets: "1",
    parts: [],
    detailItems: [],
    categoryRows: [],
    grandTotal: "0.00",
    showRuleSelector: false,
    activeRuleIndex: -1,
    activeRuleItem: null
  },

  onLoad() {
    this.loadData();
  },

  onShow() {
    const recognized = wx.getStorageSync("recognizedPartsForQuote");
    if (!recognized || !Array.isArray(recognized.parts) || !recognized.parts.length) return;

    if (this.data.loading) {
      this.pendingRecognizedParts = recognized.parts;
      return;
    }

    wx.removeStorageSync("recognizedPartsForQuote");
    this.applyRecognizedParts(recognized.parts);
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const [categories, materials, processes] = await Promise.all([
        api.request("/api/material_categories"),
        api.request("/api/materials"),
        api.request("/api/processes")
      ]);

      this.setData({
        categories,
        materials,
        processes,
        categoryNames: categories.map((item) => item.name),
        processNames: processes.map((item) => item.name),
        loading: false,
        parts: [this.createPart(categories, materials, processes)]
      }, () => {
        const recognized = this.pendingRecognizedParts || (wx.getStorageSync("recognizedPartsForQuote") || {}).parts;
        if (Array.isArray(recognized) && recognized.length) {
          this.pendingRecognizedParts = null;
          wx.removeStorageSync("recognizedPartsForQuote");
          this.applyRecognizedParts(recognized);
          return;
        }
        this.calculateNow(false);
      });
    } catch (error) {
      this.setData({ loading: false, parts: [this.createPart([], [], [])] });
      wx.showToast({ title: "数据加载失败", icon: "none" });
    }
  },

  createPart(categories = this.data.categories, materials = this.data.materials, processes = this.data.processes) {
    const categoryIndex = -1;
    const category = categories[categoryIndex];
    const filteredMaterials = category ? materials.filter((item) => item.category_id === category.id) : [];
    const materialIndex = -1;
    const processIndex = -1;

    return {
      id: makeId(),
      categoryIndex,
      categoryText: category ? category.name : "",
      filteredMaterials,
      materialNames: filteredMaterials.map(formatMaterialName),
      materialIndex,
      materialText: formatMaterialName(filteredMaterials[materialIndex]),
      processIndex,
      processText: processes[processIndex] ? processes[processIndex].name : "",
      quantity: "1",
      length: "",
      width: "",
      result: null
    };
  },

  normalizeName(value) {
    return String(value || "").replace(/[\s\-（）()【】\[\]、，,。.:：/]/g, "").toLowerCase();
  },

  findMaterialIndex(materials, recognizedPart) {
    if (!materials.length) return -1;
    if (recognizedPart.matched_material_id) {
      const matchedIndex = materials.findIndex((item) => item.id === recognizedPart.matched_material_id);
      if (matchedIndex >= 0) return matchedIndex;
    }

    const target = this.normalizeName(recognizedPart.material_name);
    if (!target) return -1;
    return materials.findIndex((item) => {
      const fullName = this.normalizeName(formatMaterialName(item));
      const name = this.normalizeName(item.name);
      return fullName.includes(target) || target.includes(name) || name.includes(target);
    });
  },

  findProcessIndex(recognizedPart) {
    if (recognizedPart.matched_process_id) {
      const matchedIndex = this.data.processes.findIndex((item) => item.id === recognizedPart.matched_process_id);
      if (matchedIndex >= 0) return matchedIndex;
    }

    const target = this.normalizeName(recognizedPart.process_name);
    if (!target) return -1;
    return this.data.processes.findIndex((item) => {
      const name = this.normalizeName(item.name);
      return name.includes(target) || target.includes(name);
    });
  },

  createPartFromRecognition(recognizedPart) {
    let categoryIndex = -1;
    if (recognizedPart.matched_category_id) {
      categoryIndex = this.data.categories.findIndex((item) => item.id === recognizedPart.matched_category_id);
    }
    if (categoryIndex < 0 && recognizedPart.material_category) {
      const categoryName = this.normalizeName(recognizedPart.material_category);
      categoryIndex = this.data.categories.findIndex((item) => this.normalizeName(item.name).includes(categoryName));
    }

    const category = this.data.categories[categoryIndex];
    let filteredMaterials = category ? this.data.materials.filter((item) => item.category_id === category.id) : this.data.materials;
    let materialIndex = this.findMaterialIndex(filteredMaterials, recognizedPart);

    if (materialIndex < 0 && recognizedPart.matched_material_id) {
      const material = this.data.materials.find((item) => item.id === recognizedPart.matched_material_id);
      if (material) {
        categoryIndex = this.data.categories.findIndex((item) => item.id === material.category_id);
        const matchedCategory = this.data.categories[categoryIndex];
        filteredMaterials = matchedCategory ? this.data.materials.filter((item) => item.category_id === matchedCategory.id) : this.data.materials;
        materialIndex = this.findMaterialIndex(filteredMaterials, recognizedPart);
      }
    }

    const processIndex = this.findProcessIndex(recognizedPart);
    const process = this.data.processes[processIndex];

    return {
      id: makeId(),
      categoryIndex,
      categoryText: this.data.categories[categoryIndex] ? this.data.categories[categoryIndex].name : "",
      filteredMaterials,
      materialNames: filteredMaterials.map(formatMaterialName),
      materialIndex,
      materialText: formatMaterialName(filteredMaterials[materialIndex]),
      processIndex,
      processText: process ? process.name : "",
      quantity: String(recognizedPart.quantity || 1),
      length: recognizedPart.length_mm ? String(recognizedPart.length_mm) : "",
      width: recognizedPart.width_mm ? String(recognizedPart.width_mm) : "",
      result: null,
      sourceName: recognizedPart.name || ""
    };
  },

  applyRecognizedParts(recognizedParts) {
    const parts = recognizedParts.map((item) => this.createPartFromRecognition(item));
    this.setData({
      parts: parts.length ? parts : [this.createPart()],
      showRuleSelector: false,
      activeRuleIndex: -1,
      activeRuleItem: null
    }, () => this.calculateNow(false));
    wx.showToast({ title: "已带入识别结果", icon: "success" });
  },

  updatePart(index, patch) {
    const parts = this.data.parts.slice();
    parts[index] = { ...parts[index], ...patch };
    this.setData({ parts }, () => this.debouncedCalculate());
  },

  onProjectSetsInput(event) {
    this.setData({ projectSets: event.detail.value }, () => this.debouncedCalculate());
  },

  onPartCategoryChange(event) {
    const index = Number(event.currentTarget.dataset.index);
    const categoryIndex = Number(event.detail.value);
    const category = this.data.categories[categoryIndex];
    const filteredMaterials = category ? this.data.materials.filter((item) => item.category_id === category.id) : [];

    this.updatePart(index, {
      categoryIndex,
      categoryText: category ? category.name : "",
      filteredMaterials,
      materialNames: filteredMaterials.map(formatMaterialName),
      materialIndex: -1,
      materialText: ""
    });
  },

  onPartMaterialChange(event) {
    const index = Number(event.currentTarget.dataset.index);
    const materialIndex = Number(event.detail.value);
    const part = this.data.parts[index];
    this.updatePart(index, {
      materialIndex,
      materialText: formatMaterialName(part.filteredMaterials[materialIndex])
    });
  },

  onPartProcessChange(event) {
    const index = Number(event.currentTarget.dataset.index);
    const processIndex = Number(event.detail.value);
    const process = this.data.processes[processIndex];
    this.updatePart(index, {
      processIndex,
      processText: process ? process.name : ""
    });
  },

  onPartInput(event) {
    const index = Number(event.currentTarget.dataset.index);
    const field = event.currentTarget.dataset.field;
    this.updatePart(index, { [field]: event.detail.value });
  },

  addPart() {
    const parts = this.data.parts.concat(this.createPart());
    this.setData({ parts }, () => this.calculateNow(false));
  },

  removePartByIndex(index) {
    if (this.data.parts.length <= 1) {
      wx.showToast({ title: "至少保留1个部件", icon: "none" });
      return;
    }

    const parts = this.data.parts.filter((_, itemIndex) => itemIndex !== index);
    this.setData({ parts }, () => this.calculateNow(false));
    wx.showToast({ title: "已删除部件", icon: "none" });
  },

  removePart(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.removePartByIndex(index);
  },

  onPartTouchStart(event) {
    const touch = event.changedTouches && event.changedTouches[0];
    if (!touch) return;
    this.partSwipeStartX = touch.clientX;
    this.partSwipeStartY = touch.clientY;
  },

  onPartTouchEnd(event) {
    const touch = event.changedTouches && event.changedTouches[0];
    if (!touch || this.partSwipeStartX === undefined) return;

    const deltaX = this.partSwipeStartX - touch.clientX;
    const deltaY = Math.abs(this.partSwipeStartY - touch.clientY);
    this.onPartTouchCancel();

    if (deltaX > 70 && deltaY < 45) {
      this.removePartByIndex(Number(event.currentTarget.dataset.index));
    }
  },

  onPartTouchCancel() {
    this.partSwipeStartX = undefined;
    this.partSwipeStartY = undefined;
  },

  debouncedCalculate() {
    clearTimeout(this.calculateTimer);
    this.calculateTimer = setTimeout(() => this.calculateNow(false), 350);
  },

  getPartPayload(part) {
    const material = part.filteredMaterials[part.materialIndex];
    const process = this.data.processes[part.processIndex];
    const length = Number(part.length);
    const width = Number(part.width);
    const quantity = Number(part.quantity || 1);
    const projectSets = Number(this.data.projectSets || 1);

    if (!material || !process || !length || !width || !quantity || !projectSets) {
      return null;
    }

    return { material, process, length, width, quantity, projectSets };
  },

  async calculatePart(part, index) {
    const payload = this.getPartPayload(part);
    if (!payload) return null;

    let standard = null;
    try {
      const match = await api.request("/api/pricing_standards/match", {
        method: "POST",
        data: {
          process_name: payload.process.name,
          material_name: payload.material.name,
          material_category_id: payload.material.category_id || "",
          material_category_name: payload.material.category_name || "",
          length: payload.length,
          width: payload.width,
          quantity: payload.quantity * payload.projectSets
        }
      });
      standard = match.standard || null;
    } catch (error) {
      standard = null;
    }

    const result = calculator.calculateQuote({ ...payload, standard });
    return {
      index: index + 1,
      name: payload.material.name,
      specification: payload.material.specification || `${payload.length}x${payload.width}mm / ${payload.process.name}`,
      quantity: payload.quantity,
      unitPrice: result.unitPrice.toFixed(2),
      totalPrice: result.totalPrice.toFixed(2),
      area: result.area.toFixed(4),
      materialCost: result.materialCost.toFixed(2),
      processCost: result.processCost.toFixed(2),
      standardName: result.standardName,
      details: result.details,
      ruleLines: buildRuleLines(payload, result)
    };
  },

  async calculateNow(showTip = true) {
    const shouldShowRules = showTip !== false;
    const items = [];
    for (let index = 0; index < this.data.parts.length; index += 1) {
      const item = await this.calculatePart(this.data.parts[index], index);
      if (item) items.push(item);
    }

    if (!items.length) {
      this.setData({
        detailItems: [],
        categoryRows: [],
        grandTotal: "0.00",
        showRuleSelector: false,
        activeRuleIndex: -1,
        activeRuleItem: null
      });
      if (shouldShowRules) wx.showToast({ title: "请先填完整参数", icon: "none" });
      return false;
    }

    const summary = buildCategoryRows(items, this.data.projectSets);
    this.setData({
      detailItems: items,
      categoryRows: summary.rows,
      grandTotal: summary.taxIncludedTotal.toFixed(2),
      showRuleSelector: shouldShowRules,
      activeRuleIndex: -1,
      activeRuleItem: null
    });
    return true;
  },

  setActiveRule(event) {
    const activeRuleIndex = Number(event.currentTarget.dataset.index);
    this.setData({
      activeRuleIndex,
      activeRuleItem: this.data.detailItems[activeRuleIndex] || null
    });
  },

  async openDetail() {
    const ready = await this.calculateNow(true);
    if (!ready) return;

    const quotation = {
      company: "太仓明邦陈列展示用品有限公司",
      title: "报价单",
      projectSets: this.data.projectSets || "1",
      date: new Date().toLocaleDateString("zh-CN"),
      itemCount: this.data.detailItems.length,
      items: this.data.detailItems,
      categoryRows: this.data.categoryRows,
      totalAmount: this.data.grandTotal
    };

    wx.setStorageSync("mobileQuotationDetail", quotation);
    wx.navigateTo({ url: "/pages/detail/detail" });
  },

  resetForm() {
    this.setData({
      projectSets: "1",
      parts: [this.createPart()],
      detailItems: [],
      categoryRows: [],
      grandTotal: "0.00",
      showRuleSelector: false,
      activeRuleIndex: -1,
      activeRuleItem: null
    }, () => this.calculateNow(false));
  }
});
