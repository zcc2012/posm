const categories = ["亚克力", "写真", "卡纸", "坑纸", "木板", "纸", "蜂窝板", "金属"];
const materialsByCategory = {
  "亚克力": [
    { name: "5mm透明亚克力（5mm亚克力）", shortName: "5mm透明亚克力", squarePrice: 0 },
    { name: "3mm透明亚克力（3mm透明亚克力）", shortName: "3mm透明亚克力", squarePrice: 80 }
  ],
  "写真": [
    { name: "180g写真纸", shortName: "180g写真纸", squarePrice: 15 },
    { name: "写真纸 低档（140g背胶+120g pp膜）", shortName: "写真纸 低档", squarePrice: 11 }
  ],
  "卡纸": [
    { name: "350g灰底白板", shortName: "350g灰底白板", squarePrice: 1.35 },
    { name: "350g单涂白卡", shortName: "350g单涂白卡", squarePrice: 2.01 },
    { name: "300g灰底白板（300g灰底白板）", shortName: "300g灰底白板", squarePrice: 1.25 },
    { name: "300g单涂白卡（300g单涂白卡）", shortName: "300g单涂白卡", squarePrice: 1.8 }
  ],
  "坑纸": [
    { name: "140芯纸+170牛皮纸（140芯纸+170牛皮纸）", shortName: "140芯纸+170牛皮纸", squarePrice: 1.95 },
    { name: "140芯纸+140牛皮纸（140芯纸+140牛皮纸）", shortName: "140芯纸+140牛皮纸", squarePrice: 1.8 }
  ],
  "木板": [
    { name: "15mm密度板（15mm）", shortName: "15mm密度板", squarePrice: 27 }
  ],
  "纸": [
    { name: "350g灰底白板+140芯纸+140牛皮纸（B 或E 瓦楞纸）", shortName: "350g灰底白板+坑纸", squarePrice: 5.1 },
    { name: "350g单涂白卡+140g芯纸+140g牛皮纸（B 或E 瓦楞纸）", shortName: "350g单涂白卡+坑纸", squarePrice: 5.85 },
    { name: "300g单涂白卡+140g芯纸+140g牛皮纸（B 或E 瓦楞纸）", shortName: "300g单涂白卡+坑纸", squarePrice: 5.6 },
    { name: "300g灰底白板+140芯纸+140牛皮纸（B 或E 瓦楞纸）", shortName: "300g灰底白板+坑纸", squarePrice: 5 }
  ],
  "蜂窝板": [
    { name: "10mm蜂窝板（10mm蜂窝板）", shortName: "10mm蜂窝板", squarePrice: 7 },
    { name: "15mm蜂窝板（15mm）", shortName: "15mm蜂窝板", squarePrice: 8.6 }
  ],
  "金属": [
    { name: "0.7mm冷轧板（0.7mm）", shortName: "0.7mm冷轧板", squarePrice: 31 }
  ]
};
const processes = ["模切", "光油", "切割", "印刷+光油+模切", "印刷+覆膜+模切", "覆膜+模切"];

let parts = [createPart()];
let latestItems = [];
let activeChoice = null;
let ruleSelectorVisible = false;
let activeRuleIndex = -1;
const mockVisionParts = [
  {
    category: "亚克力",
    materialIndex: 0,
    quantity: 1,
    process: "切割",
    length: 1200,
    width: 600,
    name: "演示侧板"
  },
  {
    category: "纸",
    materialIndex: 1,
    quantity: 2,
    process: "印刷+覆膜+模切",
    length: 800,
    width: 300,
    name: "演示画面"
  }
];

function number(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function createPart() {
  return {
    category: "",
    materialIndex: -1,
    quantity: 1,
    process: "",
    length: "",
    width: ""
  };
}

function area(length, width) {
  return ((number(length) + 30) * (number(width) + 30)) / 1000000;
}

function standardFor(type, length, width) {
  const max = Math.max(number(length), number(width));
  const min = Math.min(number(length), number(width));

  if (type === "printing") {
    if (max <= 720 && min <= 360) return { name: "4开机器", base: 200, square: 0.1 };
    if (max <= 1019 && min <= 719) return { name: "对开机", base: 1000, square: 0.2 };
    if (max <= 1419 && min <= 1019) return { name: "全开机", base: 1500, square: 1 };
    if (max <= 1620 && min <= 1220) return { name: "大全开", base: 2000, square: 0.5 };
    return { name: "大幅面印刷", base: 2000, square: 0.4 };
  }

  if (type === "cutting") {
    if (max <= 650 && min <= 450) return { name: "4开切割", base: 80, square: 0.12 };
    if (max <= 1020 && min <= 720) return { name: "对开切割", base: 120, square: 0.15 };
    if (max <= 1420 && min <= 1020) return { name: "全开切割", base: 160, square: 0.2 };
    if (max <= 1620 && min <= 1220) return { name: "大全开切割", base: 200, square: 0.25 };
    return { name: "大幅面切割", base: 160, square: 0.2 };
  }

  if (type === "die") {
    if (max <= 650 && min <= 450) return { name: "4开模切", base: 100, square: 0.15 };
    if (max <= 1020 && min <= 720) return { name: "对开模切", base: 150, square: 0.2 };
    if (max <= 1420 && min <= 1020) return { name: "全开模切", base: 200, square: 0.25 };
    if (max <= 1620 && min <= 1220) return { name: "大全开模切", base: 250, square: 0.3 };
    return { name: "大幅面模切", base: 200, square: 0.25 };
  }

  if (type === "oil") return { name: "光油", base: 80, square: 0.1 };
  if (type === "film") return { name: "覆膜", base: 100, square: 0.2 };
  return { name: "默认工艺", base: 0, square: 0 };
}

function unitForComponent(type, length, width, totalQuantity) {
  const a = area(length, width);
  const s = standardFor(type, length, width);
  if (type === "printing") {
    const overflow = Math.max(number(totalQuantity) - 3000, 0);
    return { ...s, cost: (s.base + a * s.square * overflow) / Math.max(totalQuantity, 1) };
  }
  if (type === "oil" || type === "film") return { ...s, cost: a * s.square };
  return { ...s, cost: s.base / Math.max(totalQuantity, 1) + a * s.square };
}

function selectedMaterial(part) {
  if (!part.category || part.materialIndex < 0) return null;
  const list = materialsByCategory[part.category] || [];
  return list[part.materialIndex] || null;
}

function calculatePart(part, index) {
  const material = selectedMaterial(part);
  if (!material || !part.process || !part.length || !part.width || !part.quantity) return null;
  const quantity = Math.max(number(part.quantity, 1), 1);
  const projectSets = Math.max(number(document.querySelector("#projectSets").value, 1), 1);
  const totalQuantity = quantity * projectSets;
  const a = area(part.length, part.width);
  const materialCost = a * (material?.squarePrice || 0);

  const componentTypes = [];
  if (part.process.includes("印刷")) componentTypes.push("printing");
  if (part.process.includes("光油")) componentTypes.push("oil");
  if (part.process.includes("覆膜")) componentTypes.push("film");
  if (part.process.includes("模切")) componentTypes.push("die");
  if (part.process.includes("切割")) componentTypes.push("cutting");

  const components = componentTypes.map((type) => unitForComponent(type, part.length, part.width, totalQuantity));
  const processCost = components.reduce((sum, item) => sum + item.cost, 0);
  const unitPrice = materialCost + processCost;
  const totalPrice = unitPrice * quantity;
  const details = components.length
    ? components.map((item) => `${item.name}: ¥${item.cost.toFixed(2)}`)
    : ["默认工艺：¥0.00"];
  const standardName = components.length > 1 ? "本地组合工艺默认标准" : details[0].replace(/:.*$/, "");
  const ruleLines = [
    `面积：(长 ${part.length}+30) × (宽 ${part.width}+30) ÷ 1000000 = ${a.toFixed(4)} m²`,
    `判定数量：部件数量 ${quantity} × 项目套数 ${projectSets} = ${totalQuantity}`,
    `主材料：${material.shortName || material.name}，平方单价 ¥${number(material.squarePrice).toFixed(2)}，材料单价 ¥${materialCost.toFixed(2)}`,
    `工艺标准：${standardName}`,
    ...details.map((item) => `工艺明细：${item}`),
    `单件单价：材料 ¥${materialCost.toFixed(2)} + 工艺 ¥${processCost.toFixed(2)} = ¥${unitPrice.toFixed(2)}`,
    `部件小计：单件 ¥${unitPrice.toFixed(2)} × 数量 ${quantity} = ¥${totalPrice.toFixed(2)}`
  ];

  return {
    index: index + 1,
    name: material?.shortName || "材料",
    specification: `${part.length}x${part.width}mm / ${part.process}`,
    quantity,
    materialCost,
    processCost,
    unitPrice,
    totalPrice,
    standardName,
    details,
    ruleLines
  };
}

function toMoney(value) {
  const amount = Number(value) || 0;
  return amount > 0 ? `¥${amount.toFixed(2)}` : "";
}

function buildCategoryRows(items) {
  const sets = Math.max(number(document.querySelector("#projectSets").value, 1), 1);
  const mainMaterialTotal = items.reduce((sum, item) => sum + item.materialCost * item.quantity, 0);
  const processingTotal = items.reduce((sum, item) => sum + item.processCost * item.quantity, 0);
  const costTotal = mainMaterialTotal + processingTotal;
  const managementCost = costTotal * 0.07;
  const preTaxTotal = costTotal + managementCost;
  const taxCost = preTaxTotal * 0.17;
  const taxIncludedTotal = preTaxTotal + taxCost;

  const row = (numberText, name, totalPrice = 0, className = "") => ({
    number: numberText,
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

function calculateAll(options = {}) {
  latestItems = parts.map(calculatePart).filter(Boolean);
  if (!latestItems.length) {
    ruleSelectorVisible = false;
    activeRuleIndex = -1;
  } else if (options.showRules) {
    ruleSelectorVisible = true;
    activeRuleIndex = -1;
  } else {
    ruleSelectorVisible = false;
    activeRuleIndex = -1;
  }
  const summary = buildCategoryRows(latestItems);
  document.querySelector("#grandTotal").textContent = `¥${summary.taxIncludedTotal.toFixed(2)}`;
  renderRule();
  return summary;
}

function renderRule() {
  const card = document.querySelector("#ruleCard");
  const tabs = document.querySelector("#ruleTabs");
  const price = document.querySelector("#rulePrice");
  const lines = document.querySelector("#ruleLines");
  const item = latestItems[activeRuleIndex];
  if (!ruleSelectorVisible || !latestItems.length) {
    card.hidden = true;
    return;
  }

  card.hidden = false;
  document.querySelector("#ruleSubtitle").textContent = item ? `部件 ${item.index} · ${item.name}` : "选择部件编号查看单价来源";
  price.hidden = !item;
  price.textContent = item ? `¥${item.unitPrice.toFixed(2)}` : "";
  lines.hidden = !item;
  lines.innerHTML = item ? item.ruleLines.map((line) => `<div>${line}</div>`).join("") : "";

  tabs.hidden = false;
  tabs.innerHTML = latestItems
    .map((part, index) => `<button type="button" class="rule-tab ${index === activeRuleIndex ? "is-active" : ""}" data-rule-index="${index}">${part.index}</button>`)
    .join("");
  tabs.querySelectorAll("[data-rule-index]").forEach((button) => {
    button.addEventListener("click", () => {
      activeRuleIndex = Number(button.dataset.ruleIndex);
      renderRule();
    });
  });
}

function renderParts() {
  document.querySelector("#partsList").innerHTML = parts
    .map((part, index) => {
      const material = selectedMaterial(part);
      return `
        <div class="part-row" data-index="${index}">
          <div class="part-index">${index + 1}</div>
          <button type="button" class="pick-button" data-choice="category">${part.category || "分类"}</button>
          <button type="button" class="pick-button material-pick" data-choice="material">${material?.name || "材料"}</button>
          <input type="number" min="1" value="${part.quantity}" data-field="quantity" />
          <input type="number" min="1" value="${part.length}" data-field="length" />
          <input type="number" min="1" value="${part.width}" data-field="width" />
          <button type="button" class="pick-button" data-choice="process">${part.process || "请选择工艺"}</button>
        </div>
      `;
    })
    .join("");
  bindPartEvents();
  calculateAll();
}

function bindPartEvents() {
  document.querySelectorAll("[data-index] input").forEach((input) => {
    input.addEventListener("input", () => {
      const index = Number(input.closest("[data-index]").dataset.index);
      parts[index][input.dataset.field] = input.value;
      calculateAll();
    });
  });

  document.querySelectorAll("[data-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.closest("[data-index]").dataset.index);
      openChoice(index, button.dataset.choice);
    });
  });

  document.querySelectorAll(".part-row").forEach((row) => {
    let startX = 0;
    let startY = 0;
    let tracking = false;

    row.addEventListener("pointerdown", (event) => {
      startX = event.clientX;
      startY = event.clientY;
      tracking = true;
    });

    row.addEventListener("pointerup", (event) => {
      if (!tracking) return;
      tracking = false;
      const deltaX = startX - event.clientX;
      const deltaY = Math.abs(startY - event.clientY);
      if (deltaX > 60 && deltaY < 35 && parts.length > 1) {
        const index = Number(row.dataset.index);
        parts = parts.filter((_, itemIndex) => itemIndex !== index);
        renderParts();
      }
    });

    row.addEventListener("pointercancel", () => {
      tracking = false;
    });
  });
}

function openChoice(index, type) {
  const part = parts[index];
  let title = "请选择";
  let options = [];
  let activeValue = "";

  if (type === "category") {
    title = "选择材料分类";
    options = categories.map((name) => ({ label: name, value: name }));
    activeValue = part.category;
  }

  if (type === "process") {
    title = "选择工艺";
    options = processes.map((name) => ({ label: name, value: name }));
    activeValue = part.process;
  }

  if (type === "material") {
    title = part.category ? "选择材料" : "请先选择材料分类";
    const list = materialsByCategory[part.category] || [];
    options = list.map((item, itemIndex) => ({ label: item.name, value: String(itemIndex) }));
    activeValue = String(part.materialIndex);
  }

  activeChoice = { index, type };
  document.querySelector("#choiceTitle").textContent = title;
  document.querySelector("#choiceOptions").innerHTML = options.length
    ? options
      .map((option) => `<button type="button" class="choice-option ${option.value === activeValue ? "is-active" : ""}" data-value="${option.value}">${option.label}</button>`)
      .join("")
    : '<div class="choice-option">暂无可选项</div>';

  document.querySelector("#choiceSheet").hidden = false;
  document.querySelectorAll(".choice-option[data-value]").forEach((button) => {
    button.addEventListener("click", () => applyChoice(button.dataset.value));
  });
}

function closeChoice() {
  activeChoice = null;
  document.querySelector("#choiceSheet").hidden = true;
}

function applyChoice(value) {
  if (!activeChoice) return;
  const part = parts[activeChoice.index];

  if (activeChoice.type === "category") {
    part.category = value;
    part.materialIndex = -1;
  }

  if (activeChoice.type === "process") {
    part.process = value;
  }

  if (activeChoice.type === "material") {
    part.materialIndex = Number(value);
  }

  closeChoice();
  renderParts();
}

function renderDetail() {
  const summary = calculateAll();
  document.querySelector("#detailProjectSets").textContent = document.querySelector("#projectSets").value || "1";
  document.querySelector("#detailDate").textContent = new Date().toLocaleDateString("zh-CN");
  document.querySelector("#detailCount").textContent = latestItems.length;
  document.querySelector("#detailRows").innerHTML = summary.rows
    .map((row) => `
      <div class="quote-table-row ${row.className || ""}">
        <span>${row.number}</span>
        <span>${row.name}</span>
        <span>${row.isSummary ? row.unitLines.join("<br>") : row.unitPrice}</span>
        <span>${row.isSummary ? row.totalLines.join("<br>") : row.totalPrice}</span>
      </div>
    `)
    .join("");
}

function showPage(page) {
  document.querySelectorAll(".mini-page").forEach((item) => {
    item.classList.toggle("is-active", item.id === `page-${page}`);
  });
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === (page === "detail" ? "quote" : page));
  });
  document.querySelector("#navTitle").textContent = page === "home" ? "明邦报价" : page === "detail" ? "报价明细" : page === "vision" ? "图纸识别" : "手机报价";
}

function renderVisionResult() {
  document.querySelector("#visionResult").hidden = false;
  document.querySelector("#visionParts").innerHTML = mockVisionParts
    .map((part, index) => `
      <div class="vision-part">
        <b>${index + 1}. ${part.name}</b>
        <span>${part.length} × ${part.width}mm / 数量 ${part.quantity}</span>
        <span>${part.category} · ${materialsByCategory[part.category]?.[part.materialIndex]?.shortName || "材料"} · ${part.process}</span>
      </div>
    `)
    .join("");
}

function applyVisionParts() {
  parts = mockVisionParts.map((item) => ({
    category: item.category,
    materialIndex: item.materialIndex,
    quantity: item.quantity,
    process: item.process,
    length: item.length,
    width: item.width
  }));
  renderParts();
  showPage("quote");
}

document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", () => showPage(button.dataset.tab));
});

document.querySelector("#projectSets").addEventListener("input", calculateAll);
document.querySelector("#addPartButton").addEventListener("click", () => {
  parts.push(createPart());
  renderParts();
});
document.querySelector("#resetButton").addEventListener("click", () => {
  document.querySelector("#projectSets").value = 1;
  parts = [createPart()];
  ruleSelectorVisible = false;
  activeRuleIndex = -1;
  renderParts();
});
document.querySelector("#calculateButton").addEventListener("click", () => calculateAll({ showRules: true }));
document.querySelector("#detailButton").addEventListener("click", () => {
  renderDetail();
  showPage("detail");
});
document.querySelector("#detailBack").addEventListener("click", () => showPage("quote"));
document.querySelector("#choiceMask").addEventListener("click", closeChoice);
document.querySelector("#mockCameraButton").addEventListener("click", renderVisionResult);
document.querySelector("#mockChooseButton").addEventListener("click", renderVisionResult);
document.querySelector("#mockVisionButton").addEventListener("click", renderVisionResult);
document.querySelector("#applyVisionButton").addEventListener("click", applyVisionParts);

renderParts();
