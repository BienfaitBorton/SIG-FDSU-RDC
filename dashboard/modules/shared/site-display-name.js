/**
 * Résolution centralisée du libellé métier d’un site FDSU (miroir Python).
 * Priorité : Village Name → locality → name → infra_name → site_name non technique → fallback technique.
 */
(function initSiteDisplayName(global) {
  const TECHNICAL_RE = /(?:^Part\d+_|\bNewSite\b|\bBC_\d|_C\d+$|^CD\d{3,}|^SITES_\d+_)/i;

  function asText(value) {
    if (value == null) return null;
    const text = String(value).trim();
    return text || null;
  }

  function isTechnicalSiteIdentifier(value) {
    const text = asText(value);
    if (!text) return false;
    if (TECHNICAL_RE.test(text)) return true;
    if (/NewSite/i.test(text) || /^Part\d+_/i.test(text)) return true;
    return false;
  }

  function extractTechnicalId(site) {
    const bag = site || {};
    for (const key of ['site_name', 'Site Name', 'technical_id', 'source_id']) {
      const value = asText(bag[key]);
      if (value && isTechnicalSiteIdentifier(value)) return value;
    }
    return asText(bag.site_code) || asText(bag.site_id);
  }

  const CANDIDATES = [
    ['village_name', ['Village Name', 'village_name', 'village', 'Village']],
    ['locality_name', ['locality_name', 'locality', 'Locality', 'localite', 'localité', 'localite_name']],
    ['name', ['name', 'nom', 'display_name']],
    ['infra_name', ['infra_name']],
    ['nearest_site', ['nearest_site', 'Nearest Site']],
    ['site_name', ['site_name', 'Site Name']],
  ];

  function resolveSiteDisplayName(site) {
    const props = site && typeof site.properties === 'object' ? site.properties : {};
    const bag = { ...props, ...(site || {}) };
    const technicalId = extractTechnicalId(bag);
    let chosen = null;
    let sourceField = null;

    for (const [fieldId, keys] of CANDIDATES) {
      for (const key of keys) {
        const value = asText(bag[key]);
        if (!value) continue;
        if (isTechnicalSiteIdentifier(value)) continue;
        // display_name déjà résolu côté API : l’accepter
        if (key === 'display_name' && value) {
          chosen = value;
          sourceField = bag.display_name_source || 'display_name';
          break;
        }
        chosen = value;
        sourceField = fieldId;
        break;
      }
      if (chosen) break;
    }

    if (!chosen) {
      for (const key of ['site_name', 'Site Name', 'name', 'nom', 'site_code']) {
        const value = asText(bag[key]);
        if (value) {
          chosen = value;
          sourceField = 'technical_fallback';
          break;
        }
      }
    }
    if (!chosen) {
      chosen = `Site ${bag.site_id || '—'}`;
      sourceField = 'technical_fallback';
    }

    const isFallback = sourceField === 'technical_fallback' || (technicalId && chosen === technicalId);
    return {
      display_name: chosen,
      technical_id: technicalId,
      source_field: sourceField,
      is_technical_fallback: Boolean(isFallback),
    };
  }

  function siteDisplayLabel(site) {
    if (site && asText(site.display_name) && !isTechnicalSiteIdentifier(site.display_name)) {
      return asText(site.display_name);
    }
    return resolveSiteDisplayName(site).display_name;
  }

  global.FdsuSiteDisplayName = {
    resolveSiteDisplayName,
    siteDisplayLabel,
    isTechnicalSiteIdentifier,
    extractTechnicalId,
  };
})(window);
