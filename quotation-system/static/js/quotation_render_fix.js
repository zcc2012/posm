// Render/production quotation calculation patch.
// This file is loaded after quotation_new.html's original inline script.
// It replaces the old frontend-only/special printing calculation with one unified backend-standard calculation.
(function () {
    function num(value, fallback = 0) {
        const parsed = parseFloat(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    function intNum(value, fallback = 0) {
        const parsed = parseInt(value, 10);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    function getProjectSets() {
        return Math.max(intNum(document.getElementById('projectSets')?.value, 1), 1);
    }

    function getStandardWastage(standard, quantity) {
        if (!standard) return 0;
        if (quantity <= 100) return intNum(standard.wastage_0_100 ?? standard.wastage, 0);
        if (quantity <= 3000) return intNum(standard.wastage_100_3000 ?? standard.wastage, 0);
        return intNum(standard.wastage_3000_plus ?? standard.wastage, 0);
    }

    function getOrderIncrease(standard, materialStandard, fieldName, fallback = 30) {
        const valueFromStandard = num(standard?.[fieldName], NaN);
        if (Number.isFinite(valueFromStandard) && valueFromStandard > 0) return valueFromStandard;

        const valueFromMaterial = num(materialStandard?.[fieldName], NaN);
        if (Number.isFinite(valueFromMaterial) && valueFromMaterial > 0) return valueFromMaterial;

        return fallback;
    }

    function buildStandardTooltip(result, area, actualQuantity, materialUnitCost, processUnitCost, finalUnitPrice) {
        if (!result || !result.standard) {
            const message = result?.message || '未命中判定标准，已按材料/工艺默认价格估算';
            return `<div class="standard-empty">${message}</div>`;
        }

        const standard = result.standard;
        const components = Array.isArray(standard.components) ? standard.components : [standard];
        const componentHtml = components.map((component) => {
            return `
                <div class="standard-tooltip-section">
                    <div class="standard-tooltip-name">${component.name || component.type || '判定标准'}</div>
                    <div class="standard-tooltip-line">类型：${component.type || '-'}</div>
                    <div class="standard-tooltip-line">尺寸：${component.min_length ?? 0}-${component.max_length ?? '-'} × ${component.min_width ?? 0}-${component.max_width ?? '-'} mm</div>
                    <div class="standard-tooltip-line">数量：${component.min_quantity ?? 1}-${component.max_quantity ?? '-'}</div>
                    <div class="standard-tooltip-line">基础价：${num(component.base_price).toFixed(2)}；平方价：${num(component.square_price).toFixed(4)}</div>
                </div>
            `;
        }).join('');

        return `
            <div class="standard-tooltip-title">已命中判定标准</div>
            ${componentHtml}
            <div class="standard-tooltip-formula">面积：${area.toFixed(4)}㎡；实际数量：${actualQuantity}</div>
            <div class="standard-tooltip-line">材料单价：${materialUnitCost.toFixed(2)}；工艺单价：${processUnitCost.toFixed(2)}</div>
            <div class="standard-tooltip-total">最终单价：¥${finalUnitPrice.toFixed(2)}</div>
        `;
    }

    function updateStandardTrigger(row, result, area, actualQuantity, materialUnitCost, processUnitCost, finalUnitPrice) {
        const trigger = row.querySelector('.standard-trigger');
        if (!trigger) return;

        const span = trigger.querySelector('span');
        const tooltip = trigger.querySelector('.standard-tooltip');
        const hasStandard = Boolean(result && result.standard);

        trigger.classList.toggle('has-standard', hasStandard);
        trigger.classList.toggle('is-empty', !hasStandard);

        if (span) span.textContent = hasStandard ? '已匹配' : '未匹配';
        if (tooltip) {
            tooltip.innerHTML = buildStandardTooltip(result, area, actualQuantity, materialUnitCost, processUnitCost, finalUnitPrice);
        }
    }

    function clearRow(row) {
        const priceDisplay = row.querySelector('.price-display');
        if (priceDisplay) priceDisplay.value = '';
        const trigger = row.querySelector('.standard-trigger');
        if (trigger) {
            trigger.classList.remove('has-standard');
            trigger.classList.add('is-empty');
            const span = trigger.querySelector('span');
            const tooltip = trigger.querySelector('.standard-tooltip');
            if (span) span.textContent = '计算标准';
            if (tooltip) tooltip.innerHTML = '<div class="standard-empty">填写材料、尺寸和工艺后显示</div>';
        }
    }

    async function patchedCalculatePrice(row) {
        const materialSelect = row.querySelector('.material-select');
        const quantityInput = row.querySelector('.quantity-input');
        const lengthInput = row.querySelector('.length-input');
        const widthInput = row.querySelector('.width-input');
        const processSelect = row.querySelector('.process-select');
        const priceDisplay = row.querySelector('.price-display');

        const materialOption = materialSelect?.selectedOptions?.[0];
        const processOption = processSelect?.selectedOptions?.[0];

        const materialId = materialSelect?.value;
        const processId = processSelect?.value;
        const length = num(lengthInput?.value, 0);
        const width = num(widthInput?.value, 0);
        const quantity = Math.max(num(quantityInput?.value, 1), 1);
        const projectSets = getProjectSets();
        const totalQuantity = quantity * projectSets;

        if (!materialId || !processId || !length || !width || !quantity) {
            clearRow(row);
            return;
        }

        const materialUnitBasePrice = num(materialOption?.dataset.unitPrice, 0);
        const materialSquarePrice = num(materialOption?.dataset.squarePrice, 0);
        const fallbackProcessPrice = num(processOption?.dataset.price, 0);
        const processName = processOption?.textContent || '';

        let result = null;
        try {
            const response = await fetch('/api/pricing_standards/match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    process_name: processName,
                    material_name: materialOption?.textContent || '',
                    material_category_id: materialOption?.dataset.categoryId || '',
                    material_category_name: materialOption?.dataset.categoryName || '',
                    length,
                    width,
                    quantity: totalQuantity
                })
            });

            if (!response.ok) {
                throw new Error(`判定标准接口错误：${response.status}`);
            }
            result = await response.json();
        } catch (error) {
            console.error('判定标准匹配失败：', error);
            result = { standard: null, message: error.message };
        }

        const standard = result?.standard || null;
        const materialStandard = result?.material_standard || standard?.material_standard || null;
        const orderLengthIncrease = getOrderIncrease(standard, materialStandard, 'order_length_increase', 30);
        const orderWidthIncrease = getOrderIncrease(standard, materialStandard, 'order_width_increase', 30);
        const area = ((length + orderLengthIncrease) * (width + orderWidthIncrease)) / 1000000;

        const wastage = getStandardWastage(standard, totalQuantity);
        const actualQuantity = Math.max(totalQuantity + wastage, 1);

        const materialUnitCost = materialUnitBasePrice + (area * materialSquarePrice);
        let processUnitCost = fallbackProcessPrice;

        if (standard) {
            const components = Array.isArray(standard.components) && standard.components.length ? standard.components : [standard];
            processUnitCost = components.reduce((sum, component) => {
                const basePrice = num(component.base_price, 0);
                const squarePrice = num(component.square_price, 0);
                return sum + (basePrice / actualQuantity) + (area * squarePrice);
            }, 0);
        }

        const finalUnitPrice = materialUnitCost + processUnitCost;

        if (priceDisplay) {
            priceDisplay.value = `¥${finalUnitPrice.toFixed(2)}`;
            priceDisplay.dataset.unitPrice = finalUnitPrice.toFixed(4);
            priceDisplay.dataset.materialUnitCost = materialUnitCost.toFixed(4);
            priceDisplay.dataset.processUnitCost = processUnitCost.toFixed(4);
            priceDisplay.dataset.totalQuantity = totalQuantity;
            priceDisplay.dataset.actualQuantity = actualQuantity;
        }

        row.dataset.unitPrice = finalUnitPrice.toFixed(4);
        row.dataset.materialUnitCost = materialUnitCost.toFixed(4);
        row.dataset.processUnitCost = processUnitCost.toFixed(4);
        row.dataset.matchedStandard = standard ? '1' : '0';

        updateStandardTrigger(row, result, area, actualQuantity, materialUnitCost, processUnitCost, finalUnitPrice);

        if (typeof window.saveFormData === 'function') {
            try { window.saveFormData(); } catch (error) { console.warn('保存表单状态失败：', error); }
        }
    }

    // Replace the original global function used by existing event listeners.
    window.calculatePrice = patchedCalculatePrice;
    try {
        calculatePrice = patchedCalculatePrice;
    } catch (error) {
        // Ignore in strict environments.
    }

    // Recalculate already-filled rows after the patch is loaded.
    window.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            document.querySelectorAll('.input-row').forEach((row) => {
                patchedCalculatePrice(row);
            });
        }, 800);
    });

    console.log('✅ 报价页 Render 计算修复脚本已加载');
})();
