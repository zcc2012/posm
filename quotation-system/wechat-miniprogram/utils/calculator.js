function toNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function includesAny(text, keywords) {
  const value = String(text || "").toLowerCase();
  return keywords.some((keyword) => value.includes(String(keyword).toLowerCase()));
}

function getArea(length, width) {
  return ((toNumber(length) + 30) * (toNumber(width) + 30)) / 1000000;
}

function getTieredPrintingOverflowQuantity(totalQuantity) {
  return Math.max(toNumber(totalQuantity) - 3000, 0);
}

function getTieredPrintingUnitCost(basePrice, squarePrice, area, totalQuantity) {
  const quantity = Math.max(toNumber(totalQuantity), 1);
  const overflowQuantity = getTieredPrintingOverflowQuantity(quantity);
  const overflowCost = area * toNumber(squarePrice) * overflowQuantity;
  return (toNumber(basePrice) + overflowCost) / quantity;
}

function getDefaultProcessUnitCost(basePrice, squarePrice, area, totalQuantity) {
  const quantity = Math.max(toNumber(totalQuantity), 1);
  return toNumber(basePrice) / quantity + area * toNumber(squarePrice);
}

function getLocalProcessStandard(processType, length, width) {
  const maxDimension = Math.max(toNumber(length), toNumber(width));
  const minDimension = Math.min(toNumber(length), toNumber(width));

  if (processType === "printing") {
    if (maxDimension <= 720 && minDimension <= 360) return { name: "4开机器", basePrice: 200, squarePrice: 0.1 };
    if (maxDimension <= 1019 && minDimension <= 719) return { name: "对开机", basePrice: 1000, squarePrice: 0.2 };
    if (maxDimension <= 1419 && minDimension <= 1019) return { name: "全开机", basePrice: 1500, squarePrice: 1 };
    if (maxDimension <= 1620 && minDimension <= 1220) return { name: "大全开", basePrice: 2000, squarePrice: 0.5 };
    return { name: "大幅面印刷", basePrice: 2000, squarePrice: 0.4 };
  }

  if (processType === "die-cutting") {
    if (maxDimension <= 650 && minDimension <= 450) return { name: "4开模切", basePrice: 100, squarePrice: 0.15 };
    if (maxDimension <= 1020 && minDimension <= 720) return { name: "对开模切", basePrice: 150, squarePrice: 0.2 };
    if (maxDimension <= 1420 && minDimension <= 1020) return { name: "全开模切", basePrice: 200, squarePrice: 0.25 };
    if (maxDimension <= 1620 && minDimension <= 1220) return { name: "大全开模切", basePrice: 250, squarePrice: 0.3 };
    return { name: "大幅面模切", basePrice: 200, squarePrice: 0.25 };
  }

  if (processType === "cutting") {
    if (maxDimension <= 650 && minDimension <= 450) return { name: "4开切割", basePrice: 80, squarePrice: 0.12 };
    if (maxDimension <= 1020 && minDimension <= 720) return { name: "对开切割", basePrice: 120, squarePrice: 0.15 };
    if (maxDimension <= 1420 && minDimension <= 1020) return { name: "全开切割", basePrice: 160, squarePrice: 0.2 };
    if (maxDimension <= 1620 && minDimension <= 1220) return { name: "大全开切割", basePrice: 200, squarePrice: 0.25 };
    return { name: "大幅面切割", basePrice: 160, squarePrice: 0.2 };
  }

  if (processType === "varnish") {
    if (maxDimension <= 650 && minDimension <= 450) return { name: "4开光油", basePrice: 80, squarePrice: 0.1 };
    if (maxDimension <= 1020 && minDimension <= 720) return { name: "对开光油", basePrice: 120, squarePrice: 0.15 };
    if (maxDimension <= 1420 && minDimension <= 1020) return { name: "全开光油", basePrice: 150, squarePrice: 0.2 };
    if (maxDimension <= 1620 && minDimension <= 1220) return { name: "大全开光油", basePrice: 180, squarePrice: 0.25 };
    return { name: "大幅面光油", basePrice: 150, squarePrice: 0.2 };
  }

  if (processType === "lamination") {
    if (maxDimension <= 650 && minDimension <= 450) return { name: "4开覆膜", basePrice: 100, squarePrice: 0.2 };
    if (maxDimension <= 1020 && minDimension <= 720) return { name: "对开覆膜", basePrice: 150, squarePrice: 0.25 };
    if (maxDimension <= 1420 && minDimension <= 1020) return { name: "全开覆膜", basePrice: 200, squarePrice: 0.3 };
    if (maxDimension <= 1620 && minDimension <= 1220) return { name: "大全开覆膜", basePrice: 250, squarePrice: 0.35 };
    return { name: "大幅面覆膜", basePrice: 180, squarePrice: 0.3 };
  }

  return { name: "标准工艺", basePrice: 0, squarePrice: 0 };
}

function getSelectedProcessComponents(processName, length, width) {
  const rules = [
    { keyword: "印刷", type: "printing", name: "印刷" },
    { keyword: "模切", type: "die-cutting", name: "模切" },
    { keyword: "切割", type: "cutting", name: "切割" },
    { keyword: "光油", type: "varnish", name: "光油" },
    { keyword: "覆膜", type: "lamination", name: "覆膜" },
    { keyword: "光膜", type: "lamination", name: "光膜" }
  ];

  return rules.reduce((items, rule) => {
    if (!String(processName || "").includes(rule.keyword)) return items;
    if (items.some((item) => item.type === rule.type)) return items;
    const fallback = getLocalProcessStandard(rule.type, length, width);
    items.push({
      type: rule.type,
      name: fallback.name,
      base_price: fallback.basePrice,
      square_price: fallback.squarePrice
    });
    return items;
  }, []);
}

function isPrintingComponent(component) {
  return includesAny(`${component.type} ${component.name}`, ["printing", "印刷"]);
}

function getComponentUnitCost(component, area, totalQuantity) {
  if (isPrintingComponent(component)) {
    return getTieredPrintingUnitCost(component.base_price, component.square_price, area, totalQuantity);
  }

  if (includesAny(`${component.type} ${component.name}`, ["varnish", "lamination", "光油", "覆膜", "光膜"])) {
    return area * toNumber(component.square_price);
  }

  return getDefaultProcessUnitCost(component.base_price, component.square_price, area, totalQuantity);
}

function calculateQuote(input) {
  const material = input.material || {};
  const process = input.process || {};
  const length = toNumber(input.length);
  const width = toNumber(input.width);
  const quantity = Math.max(toNumber(input.quantity, 1), 1);
  const projectSets = Math.max(toNumber(input.projectSets, 1), 1);
  const totalQuantity = quantity * projectSets;
  const area = getArea(length, width);
  const materialCost = area * toNumber(material.square_price);
  const processName = process.name || "";
  const standard = input.standard || null;

  let processCost = 0;
  let standardName = "";
  let details = [];

  if (standard && standard.type === "combined" && Array.isArray(standard.components)) {
    details = standard.components.map((component) => {
      const unitCost = getComponentUnitCost(component, area, totalQuantity);
      processCost += unitCost;
      return `${component.name || component.type}: ¥${unitCost.toFixed(2)}`;
    });
    standardName = standard.name || "组合工艺判定标准";
  } else if (standard) {
    processCost = getComponentUnitCost(standard, area, totalQuantity);
    details = [`${standard.name || "判定标准"}: ¥${processCost.toFixed(2)}`];
    standardName = standard.name || "已匹配判定标准";
  } else {
    const components = getSelectedProcessComponents(processName, length, width);
    if (components.length > 0) {
      details = components.map((component) => {
        const unitCost = getComponentUnitCost(component, area, totalQuantity);
        processCost += unitCost;
        return `${component.name}: ¥${unitCost.toFixed(2)}`;
      });
      standardName = components.length > 1 ? "本地组合工艺默认标准" : components[0].name;
    } else {
      processCost = getDefaultProcessUnitCost(process.base_price, process.square_price, area, totalQuantity);
      details = [`选项价格: ¥${processCost.toFixed(2)}`];
      standardName = "默认选项价格";
    }
  }

  const unitPrice = materialCost + processCost;
  const totalPrice = unitPrice * quantity;

  return {
    area,
    materialCost,
    processCost,
    unitPrice,
    totalPrice,
    totalQuantity,
    standardName,
    details
  };
}

module.exports = {
  calculateQuote
};
