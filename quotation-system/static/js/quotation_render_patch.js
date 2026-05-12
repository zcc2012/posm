// Render / online quotation page price-display patch.
// Purpose: keep the unit price box from staying at the placeholder "自动计算" when the
// original inline calculatePrice function fails before assigning priceDisplay.value.
(function () {
    console.log('[quotation-render-patch] loaded');

    function toNumber(value, defaultValue = 0) {
        const number = parseFloat(value);
        return Number.isFinite(number) ? number : defaultValue;
    }

    function getProjectSets() {
        const input = document.getElementById('projectSets');
        return Math.max(parseInt(input && input.value, 10) || 1, 1);
    }

    function getWastageFromStandard(standard, quantity) {
        if (!standard) return 0;
        if (quantity <= 100) return toNumber(standard.wastage_0_100 ?? standard.wastage, 0);
        if (quantity <= 3000) return toNumber(standard.wastage_100_3000 ?? standard.wastage, 0);
        return toNumber(standard.wastage_3000_plus ?? standard.wastage, 0);
    }

    function buildStandardTooltip(result, standard, unitPrice) {
        if (!result || !standard) {
            const message = result && result.message ? result.message : '未命中判定标准';
            return '<div class="standard-tooltip-title">未命中标准</div>' +
                '<div class="standard-tooltip-line">' + message + '</div>';
        }

        const components = Array.isArray(standard.components) ? standard.components : [standard];
        const componentHtml = components.map(function (component) {
            return '<div class="standard-tooltip-section process-cost">' +
                '<div class="standard-tooltip-name">' + (component.name || component.type || '工艺标准') + '</div>' +
                '<div class="standard-tooltip-line">类型：' + (component.type || '-') + '</div>' +
                '<div class="standard-tooltip-line">尺寸：' +
                    (component.min_length ?? 0) + '-' + (component.max_length ?? '-') + ' × ' +
                    (component.min_width ?? 0) + '-' + (component.max_width ?? '-') + ' mm</div>' +
                '<div class="standard-tooltip-line">数量：' +
                    (component.min_quantity ?? 1) + '-' + (component.max_quantity ?? '-') + '</div>' +
                '<div class="standard-tooltip-formula">基础价：¥' + toNumber(component.base_price, 0).toFixed(2) +
                    '，平方价：¥' + toNumber(component.square_price, 0).toFixed(4) + '/㎡</div>' +
                '</div>';
        }).join('');

        return '<div class="standard-tooltip-title">已命中判定标准</div>' +
            componentHtml +
            '<div class="standard-tooltip-total">最终单价：¥' + unitPrice.toFixed(4) + ' / 件</div>';
    }

    function updateStandardTrigger(row, result, standard, unitPrice) {
        const trigger = row.querySelector('.standard-trigger');
        if (!trigger) return;

        const span = trigger.querySelector('span');
        const tooltip = trigger.querySelector('.standard-tooltip');
        trigger.classList.remove('is-empty');

        if (standard) {
            trigger.classList.add('has-standard');
            if (span) span.textContent = '计算标准';
        } else {
            trigger.classList.remove('has-standard');
            trigger.classList.add('is-empty');
            if (span) span.textContent = '未命中';
        }

        if (tooltip) {
            tooltip.innerHTML = buildStandardTooltip(result, standard, unitPrice || 0);
        }
    }

    function calculateMaterialUnitPrice(materialOption, length, width, standard) {
        const unitPrice = toNumber(materialOption.dataset.unitPrice, 0);
        const squarePrice = toNumber(materialOption.dataset.squarePrice, 0);
        const lengthIncrease = toNumber(standard && standard.order_length_increase, 30);
        const widthIncrease = toNumber(standard && standard.order_width_increase, 30);
        const area = ((length + lengthIncrease) * (width + widthIncrease)) / 1000000;
        return unitPrice + area * squarePrice;
    }

    function calculateProcessUnitPrice(standard, length, width, totalQuantity) {
        if (!standard) return 0;
        const components = Array.isArray(standard.components) && standard.components.length ? standard.components : [standard];
        let total = 0;

        components.forEach(function (component) {
            const wastage = getWastageFromStandard(component, totalQuantity);
            const actualQuantity = Math.max(totalQuantity + wastage, 1);
            const lengthIncrease = toNumber(component.order_length_increase, 0);
            const widthIncrease = toNumber(component.order_width_increase, 0);
            const area = ((length + lengthIncrease) * (width + widthIncrease)) / 1000000;
            const basePrice = toNumber(component.base_price, 0);
            const squarePrice = toNumber(component.square_price, 0);

            // Unified unit-price formula: spread base price by actual quantity, then add area-based cost.
            total += (basePrice / actualQuantity) + (area * squarePrice);
        });

        return total;
    }

    async function patchedCalculatePrice(row) {
        const materialSelect = row.querySelector('.material-select');
        const quantityInput = row.querySelector('.quantity-input');
        const lengthInput = row.querySelector('.length-input');
        const widthInput = row.querySelector('.width-input');
        const processSelect = row.querySelector('.process-select');
        const priceDisplay = row.querySelector('.price-display');

        if (!materialSelect || !quantityInput || !lengthInput || !widthInput || !processSelect || !priceDisplay) return;

        const materialOption = materialSelect.selectedOptions && materialSelect.selectedOptions[0];
        const processOption = processSelect.selectedOptions && processSelect.selectedOptions[0];
        const length = toNumber(lengthInput.value, 0);
        const width = toNumber(widthInput.value, 0);
        const quantity = toNumber(quantityInput.value, 1);

        if (!materialSelect.value || !processSelect.value || !length || !width || !quantity) {
            priceDisplay.value = '';
            updateStandardTrigger(row, { message: '填写材料、数量、长宽和工艺后自动计算' }, null, 0);
            return;
        }

        const projectSets = getProjectSets();
        const totalQuantity = Math.max(quantity * projectSets, 1);

        try {
            const response = await fetch('/api/pricing_standards/match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    process_name: processOption ? processOption.textContent || '' : '',
                    material_name: materialOption ? materialOption.textContent || '' : '',
                    material_category_id: materialOption ? materialOption.dataset.categoryId || '' : '',
                    material_category_name: materialOption ? materialOption.dataset.categoryName || '' : '',
                    length: length,
                    width: width,
                    quantity: totalQuantity
                })
            });

            const result = await response.json();
            console.log('[quotation-render-patch] match result:', result);

            if (!response.ok || !result.standard) {
                priceDisplay.value = '未命中标准';
                updateStandardTrigger(row, result, null, 0);
                return;
            }

            const standard = result.standard;
            const materialStandard = result.material_standard || standard.material_standard || null;
            const materialUnitPrice = calculateMaterialUnitPrice(materialOption, length, width, materialStandard);
            const processUnitPrice = calculateProcessUnitPrice(standard, length, width, totalQuantity);
            const finalUnitPrice = materialUnitPrice + processUnitPrice;

            priceDisplay.value = finalUnitPrice.toFixed(4);
            priceDisplay.dataset.unitPrice = finalUnitPrice.toFixed(6);
            priceDisplay.dataset.materialUnitPrice = materialUnitPrice.toFixed(6);
            priceDisplay.dataset.processUnitPrice = processUnitPrice.toFixed(6);
            priceDisplay.dataset.standard = JSON.stringify(standard);
            priceDisplay.dataset.matchResult = JSON.stringify(result);

            updateStandardTrigger(row, result, standard, finalUnitPrice);

            if (typeof window.saveFormData === 'function') {
                window.saveFormData();
            }
        } catch (error) {
            console.error('[quotation-render-patch] calculate failed:', error);
            priceDisplay.value = '计算失败';
            updateStandardTrigger(row, { message: error.message || '计算接口异常' }, null, 0);
        }
    }

    function installPatch() {
        window.originalCalculatePrice = window.calculatePrice;
        window.calculatePrice = patchedCalculatePrice;
        console.log('[quotation-render-patch] calculatePrice patched');

        document.querySelectorAll('.input-row').forEach(function (row) {
            ['change', 'input'].forEach(function (eventName) {
                row.addEventListener(eventName, function (event) {
                    if (event.target && event.target.matches('.material-select, .quantity-input, .length-input, .width-input, .process-select')) {
                        patchedCalculatePrice(row);
                    }
                }, true);
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', installPatch);
    } else {
        installPatch();
    }
})();
