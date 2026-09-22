(function () {
    'use strict';
    var FEATURE = 'DriftkingsHangarEfficiency';
    if (window.__dkHangarEfficiency) { window.__dkHangarEfficiency.dispose(); }
    var disposed = false, card = null, model = null, resourceId = null;
    var callbackId = null, pending = null, lastPayload = null, data = {};
    function number(value) { value = Number(value); return isFinite(value) ? value : 0; }
    function position() {
        if (!card) { return; }
        var cfg = data.config || {}, unit = parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 1;
        var left = (window.innerWidth - card.offsetWidth) / 2 + number(cfg.x) * unit;
        var top = window.innerHeight - card.offsetHeight - 210 * unit + number(cfg.y) * unit;
        card.style.left = Math.max(0, Math.min(window.innerWidth - card.offsetWidth, left)) + 'px';
        card.style.top = Math.max(0, Math.min(window.innerHeight - card.offsetHeight, top)) + 'px';
    }
    function element(tag, cls, parent, value) {
        var node = document.createElement(tag); node.className = cls;
        if (value !== undefined) { node.textContent = value; }
        parent.appendChild(node); return node;
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

    function render() {
        pending = null;
        if (disposed) { return; }
        readModel();
        if (!card) { card = element('div', 'dk-hangar-efficiency', document.body); }
        var rows = data.rows || [], visible = (data.config || {}).visible && rows.length;
        card.style.display = visible ? 'block' : 'none';
        if (!visible) { return; }
        while (card.firstChild) { card.removeChild(card.firstChild); }
        element('div', 'dk-he-vehicle', card, data.vehicle || '');
        var list = element('div', 'dk-he-stats', card);
        rows.forEach(function (row) {
            var item = element('div', 'dk-he-stat', list);
            if (row.icon) { var icon = element('img', 'dk-he-icon', item); icon.src = row.icon; icon.alt = ''; }
            var text = element('div', 'dk-he-text', item);
            element('div', 'dk-he-label', text, row.label);
            element('div', 'dk-he-value', text, row.value);
        });
        position();
    }
    function schedule() { if (!disposed && pending === null) { pending = setTimeout(render, 0); } }
    function dispose() {
        if (disposed) { return; }
        disposed = true;
        if (pending !== null) { clearTimeout(pending); }
        engine.off('viewEnv.onDataChanged', schedule);
        engine.off('subViews.onAdded', schedule);
        engine.off('subViews.onRemoved', schedule);
        releaseModel();
        window.removeEventListener('resize', position);
        window.removeEventListener('unload', dispose);
        if (card && card.parentNode) { card.parentNode.removeChild(card); }
        card = null;
    }
    window.__dkHangarEfficiency = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', schedule);
        engine.on('subViews.onAdded', schedule);
        engine.on('subViews.onRemoved', schedule);
        window.addEventListener('resize', position);
        window.addEventListener('unload', dispose);
        schedule();
    });
}());
