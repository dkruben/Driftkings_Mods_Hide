(function () {
    'use strict';
    var FEATURE = 'DriftkingsMarksOnGunHangar';
    if (window.__dkHangarMarks) { window.__dkHangarMarks.dispose(); }
    var disposed = false, card = null, fields = {}, model = null, resourceId = null;
    var callbackId = null, pending = null, lastPayload = null, data = {}, drag = null;

    function number(value, fallback, min, max) {
        var result = Number(value);
        return isFinite(result) ? Math.max(min, Math.min(max, result)) : fallback;
    }
    function unit() {
        return parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 1;
    }
    function color(value, fallback) {
        if (typeof value === 'number' && isFinite(value)) {
            return '#' + ('000000' + Math.max(0, Math.min(16777215, value)).toString(16)).slice(-6);
        }
        return /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
    }
    function element(tag, cls, parent, text) {
        var node = document.createElement(tag);
        node.className = 'dk-hangar-marks__' + cls;
        if (text !== undefined) { node.textContent = text; }
        parent.appendChild(node);
        return node;
    }
    function createCard() {
        card = document.createElement('div');
        card.className = 'dk-hangar-marks';
        fields.header = element('div', 'header', card);
        fields.eyebrow = element('span', 'eyebrow', fields.header, 'MARKS OF EXCELLENCE');
        fields.hint = element('span', 'hint', fields.header, 'DRAG');
        fields.vehicle = element('div', 'vehicle', card);
        var main = element('div', 'main', card);
        fields.percent = element('div', 'percent', main);
        var marks = element('div', 'marks', main);
        fields.marks = [65, 85, 95].map(function (limit) { return element('span', 'mark', marks, limit + '%'); });
        fields.bar = element('div', 'bar', card);
        fields.fill = element('div', 'fill', fields.bar);
        [65, 85, 95].forEach(function (limit) { element('i', 'tick', fields.bar).style.left = limit + '%'; });
        fields.target = element('div', 'target', card);
        var secondary = element('div', 'secondary', card);
        fields.average = element('div', 'detail', secondary);
        fields.history = element('div', 'detail', secondary);
        fields.note = element('div', 'muted', secondary, 'Estimate only; not the damage required next battle.');
        var stats = element('div', 'stats', card);
        var mastery = element('div', 'mastery', stats);
        fields.icon = element('img', 'icon', mastery);
        fields.mastery = element('span', 'stat', mastery);
        var wn8 = element('div', 'stat', stats);
        element('span', 'muted', wn8, 'WN8'); fields.wn8 = element('span', 'value', wn8);
        var wins = element('div', 'stat', stats);
        fields.winRateLabel = element('span', 'muted', wins, 'WIN RATE'); fields.wins = element('span', 'value', wins);
        fields.footer = element('div', 'footer', card);
        fields.header.addEventListener('mousedown', startDrag);
        // Only the card consumes input; the rest of the hangar remains interactive.
        card.addEventListener('mousedown', stop);
        card.addEventListener('click', stop);
        document.body.appendChild(card);
    }
    function stop(event) { event.stopPropagation(); }
    function position() {
        if (!card || drag) { return; }
        var cfg = data.config || {}, scale = unit();
        var width = card.offsetWidth, height = card.offsetHeight;
        var x = number(cfg.x, 215, -7680, 7680) * scale;
        var y = number(cfg.y, -246, -4320, 4320) * scale;
        if (cfg.alignX === 'right') { x += window.innerWidth - width; }
        else if (cfg.alignX === 'center') { x += (window.innerWidth - width) / 2; }
        if (cfg.alignY === 'bottom') { y += window.innerHeight - height; }
        else if (cfg.alignY === 'center') { y += (window.innerHeight - height) / 2; }
        card.style.left = Math.max(0, Math.min(window.innerWidth - width, x)) + 'px';
        card.style.top = Math.max(0, Math.min(window.innerHeight - height, y)) + 'px';
    }
    function releaseModel() {
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        callbackId = null; resourceId = null; model = null; lastPayload = null;
    }
    function readModel() {
        var found = null, id = null;
        if (window.subViews) {
            var ids = window.subViews.ids();
            for (var i = 0; i < ids.length; i++) {
                var child = window.subViews.get(ids[i]);
                if (child && child.model && child.model.ModInjectModel && child.model.ModInjectModel.name === FEATURE) {
                    found = child.model; id = ids[i]; break;
                }
            }
        }
        if (!found) { releaseModel(); data = {}; return; }
        if (resourceId !== id) {
            releaseModel(); resourceId = id;
            callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
        }
        model = found;
        if (lastPayload !== model.payload) {
            lastPayload = model.payload;
            try { data = JSON.parse(model.payload || '{}'); } catch (error) { data = {}; }
        }
    }
    function label(key, fallback) { return (data.labels || {})[key] || fallback; }
    function render() {
        pending = null;
        if (disposed) { return; }
        readModel();
        if (!card) { createCard(); }
        var cfg = data.config || {};
        card.style.display = cfg.visible ? 'block' : 'none';
        if (!cfg.visible) { drag = null; return; }
        card.className = 'dk-hangar-marks' + (cfg.compactMode ? ' dk-hangar-marks--compact' : '') + (cfg.locked ? ' dk-hangar-marks--locked' : '');
        card.style.width = number(cfg.width, 362, 320, 700) + 'rem';
        card.style.minHeight = number(cfg.height, 260, 160, 700) + 'rem';
        var bg = color(cfg.backgroundColor, '#0c0f14');
        card.style.backgroundColor = 'rgba(' + parseInt(bg.slice(1, 3), 16) + ',' + parseInt(bg.slice(3, 5), 16) + ',' + parseInt(bg.slice(5, 7), 16) + ',' + number(cfg.backgroundAlpha, .94, 0, 1) + ')';
        card.style.borderColor = color(cfg.outlineColor, '#4b515b');
        card.style.color = color(cfg.titleColor, '#f5f1e8');
        fields.eyebrow.style.color = color(cfg.headerColor, '#c7a86a');
        fields.target.style.color = fields.fill.style.backgroundColor = color(cfg.accentColor, '#e2c07a');
        fields.eyebrow.textContent = label('header', 'MARKS OF EXCELLENCE');
        fields.hint.textContent = cfg.locked ? label('locked', 'LOCKED') : label('drag', 'DRAG');
        fields.note.textContent = label('estimateNote', 'Estimate only; not the damage required next battle.');
        fields.winRateLabel.textContent = label('winRate', 'WIN RATE');
        fields.vehicle.textContent = data.vehicle || label('chooseVehicle', 'Choose a tank');
        var target = data.target || {}, eligible = data.state === 'data' && target.eligible;
        var percent = number(target.percent, 0, 0, 100);
        fields.percent.textContent = eligible ? percent.toFixed(2) + '%' : '--';
        fields.bar.style.display = eligible ? 'block' : 'none';
        fields.fill.style.width = percent + '%';
        fields.marks.forEach(function (badge, i) {
            var earned = data.earnedMarks > i;
            var near = target.mark === i + 1 && !target.achieved && target.gap <= number(cfg.starAnimationWindow, 5, 0, 100);
            badge.style.display = eligible ? 'block' : 'none';
            badge.className = 'dk-hangar-marks__mark' + (earned ? ' dk-hangar-marks__mark--earned' : '') + (near ? ' dk-hangar-marks__mark--near' : '');
            badge.style.color = earned ? color(cfg['starColor' + [65, 85, 95][i]], '#e2c07a') : color(cfg.mutedColor, '#8c919a');
        });
        fields.target.textContent = data.state !== 'data' ? data.message : !eligible ? label('tierLimit', 'Marks available from tier V') :
            label('mark', 'Mark') + ' ' + target.mark + ' / ' + target.threshold + '%  |  ' + (target.achieved ? label('achieved', 'Achieved') : Number(target.gap).toFixed(2) + ' ' + label('remaining', 'pp remaining'));
        fields.average.textContent = eligible ? label('average', 'Combined EMA') + ': ' + data.average + '  |  ' + label('estimate', 'Goal estimate') + ': ' + data.estimate : '';
        var recent = data.recent || {};
        fields.history.textContent = !eligible ? '' : recent.delta === null || recent.delta === undefined ? label('historyWaiting', 'History: waiting for the next battle') :
            (recent.delta >= 0 ? '+' : '') + Number(recent.delta).toFixed(2) + ' pp / ' + recent.battles + ' ' + label('observedBattles', 'battles observed');
        fields.note.style.display = eligible ? 'block' : 'none';
        fields.mastery.textContent = data.mastery || '--';
        fields.icon.style.display = data.masteryIcon ? 'block' : 'none';
        if (data.masteryIcon) { fields.icon.src = data.masteryIcon; fields.icon.alt = data.mastery; }
        fields.wn8.textContent = data.wn8 || '--'; fields.wn8.style.color = color(data.wn8Color, '#8c919a');
        fields.wins.textContent = data.winRate || '--'; fields.wins.style.color = color(data.winRateColor, '#8c919a');
        fields.footer.textContent = data.state === 'data' ? data.battles + ' ' + label('battles', 'battles') : label('noStats', 'No statistics loaded');
        position();
    }
    function schedule() { if (!disposed && pending === null) { pending = setTimeout(render, 0); } }
    function startDrag(event) {
        if (event.button !== 0 || (data.config || {}).locked || !model) { return; }
        var rect = card.getBoundingClientRect();
        drag = {x: event.clientX, y: event.clientY, left: rect.left, top: rect.top};
        event.preventDefault(); event.stopPropagation();
    }
    function moveDrag(event) {
        if (!drag) { return; }
        card.style.left = Math.max(0, Math.min(window.innerWidth - card.offsetWidth, drag.left + event.clientX - drag.x)) + 'px';
        card.style.top = Math.max(0, Math.min(window.innerHeight - card.offsetHeight, drag.top + event.clientY - drag.y)) + 'px';
        event.preventDefault(); event.stopPropagation();
    }
    function endDrag(event) {
        if (!drag) { return; }
        drag = null;
        var cfg = data.config || {}, x = parseFloat(card.style.left), y = parseFloat(card.style.top);
        if (cfg.alignX === 'right') { x -= window.innerWidth - card.offsetWidth; }
        else if (cfg.alignX === 'center') { x -= (window.innerWidth - card.offsetWidth) / 2; }
        if (cfg.alignY === 'bottom') { y -= window.innerHeight - card.offsetHeight; }
        else if (cfg.alignY === 'center') { y -= (window.innerHeight - card.offsetHeight) / 2; }
        cfg.x = Math.round(x / unit()); cfg.y = Math.round(y / unit());
        if (model && typeof model.onSavePosition === 'function') { model.onSavePosition({x: cfg.x, y: cfg.y}); }
        event.stopPropagation();
    }
    function dispose() {
        if (disposed) { return; }
        disposed = true; drag = null;
        if (pending !== null) { clearTimeout(pending); }
        engine.off('viewEnv.onDataChanged', schedule);
        engine.off('subViews.onAdded', schedule);
        engine.off('subViews.onRemoved', schedule);
        releaseModel();
        window.removeEventListener('resize', position);
        window.removeEventListener('unload', dispose);
        document.removeEventListener('mousemove', moveDrag);
        document.removeEventListener('mouseup', endDrag);
        if (card && card.parentNode) { card.parentNode.removeChild(card); }
        card = null;
    }
    window.__dkHangarMarks = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', schedule);
        engine.on('subViews.onAdded', schedule);
        engine.on('subViews.onRemoved', schedule);
        window.addEventListener('resize', position);
        window.addEventListener('unload', dispose);
        document.addEventListener('mousemove', moveDrag);
        document.addEventListener('mouseup', endDrag);
        schedule();
    });
}());
