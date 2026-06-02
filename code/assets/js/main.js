(function () {
  const data = window.siteData || window.testSiteData;
  if (!data) {
    console.warn("No site data found. Expected window.siteData.");
    return;
  }

  const byId = (id) => document.getElementById(id);

  function setSeo() {
    if (data.seo && data.seo.title) {
      document.title = data.seo.title;
    }

    if (data.seo && data.seo.description) {
      let meta = document.querySelector('meta[name="description"]');
      if (!meta) {
        meta = document.createElement("meta");
        meta.name = "description";
        document.head.appendChild(meta);
      }
      meta.content = data.seo.description;
    }
  }

  function safeExternalLink(anchor, href) {
    const normalizedHref = typeof href === "string" ? href.trim() : "";
    if (!normalizedHref) {
      anchor.removeAttribute("href");
      return;
    }

    anchor.href = normalizedHref;
    if (/^https?:\/\//i.test(normalizedHref)) {
      anchor.target = "_blank";
      anchor.rel = "noreferrer";
    }
  }

  function formatBrandName(fullName) {
    if (!fullName) {
      return "Profile";
    }
    const parts = fullName.trim().split(/\s+/);
    if (parts.length < 2) {
      return fullName;
    }
    return `${parts[0].charAt(0)}. ${parts.slice(1).join(" ")}`;
  }

  function renderSplitHeroName(node, fullName) {
    if (!node) {
      return;
    }

    node.textContent = "";

    if (!fullName) {
      return;
    }

    const parts = fullName.trim().split(/\s+/);
    if (parts.length < 2) {
      node.textContent = fullName;
      return;
    }

    const first = parts[0];
    const rest = parts.slice(1).join(" ");

    node.appendChild(document.createTextNode(first));
    node.appendChild(document.createElement("br"));

    const emphasis = document.createElement("em");
    emphasis.textContent = rest;
    node.appendChild(emphasis);
  }

  function renderNavigation() {
    const brand = byId("brandText");
    const navList = byId("navList");

    if (brand && data.identity && data.identity.name) {
      brand.textContent = formatBrandName(data.identity.name);
    }

    if (!navList || !Array.isArray(data.navigation)) {
      return;
    }

    navList.textContent = "";

    const homeItem = document.createElement("li");
    const homeLink = document.createElement("a");
    homeLink.href = "#hero";
    homeLink.textContent = "Home";
    homeItem.appendChild(homeLink);
    navList.appendChild(homeItem);

    data.navigation.forEach((item) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#${item.id}`;
      a.textContent = item.label;
      li.appendChild(a);
      navList.appendChild(li);
    });
  }

  function renderHero() {
    const heroData = data.hero || {};
    const eyebrow = byId("heroEyebrow");
    const heroName = byId("heroName");
    const heroTitle = byId("heroTitle");
    const heroSummary = byId("heroSummary");
    const heroActions = byId("heroActions");

    if (eyebrow && heroData.eyebrow) {
      eyebrow.textContent = `// ${heroData.eyebrow}`;
    }

    renderSplitHeroName(heroName, data.identity && data.identity.name);

    if (heroTitle && heroData.role) {
      heroTitle.textContent = heroData.role;
    }

    if (heroSummary && heroData.summary) {
      heroSummary.textContent = heroData.summary;
    }

    if (!heroActions || !Array.isArray(heroData.actions)) {
      return;
    }

    heroActions.textContent = "";

    heroData.actions.forEach((action, index) => {
      const link = document.createElement("a");
      link.textContent = action.label;
      link.className = index === 0 ? "btn" : "btn btn-ghost";
      safeExternalLink(link, action.href);
      heroActions.appendChild(link);
    });
  }

  function renderAbout() {
    const copyWrap = byId("aboutCopy");
    const skillsWrap = byId("skillsList");

    if (copyWrap && data.about && Array.isArray(data.about.paragraphs)) {
      data.about.paragraphs.forEach((paragraph) => {
        const p = document.createElement("p");
        p.textContent = paragraph;
        copyWrap.appendChild(p);
      });
    }

    if (skillsWrap && data.about && Array.isArray(data.about.skills)) {
      data.about.skills.forEach((skill) => {
        const skillTag = document.createElement("span");
        skillTag.className = "skill-tag";
        skillTag.textContent = skill;
        skillsWrap.appendChild(skillTag);
      });
    }
  }

  function renderQuickFacts() {
    const factsWrap = byId("quickFacts");
    if (!factsWrap || !Array.isArray(data.quickFacts)) {
      return;
    }

    data.quickFacts.forEach((fact) => {
      const row = document.createElement("div");
      row.className = "info-row";

      const icon = document.createElement("div");
      icon.className = "info-icon";
      icon.textContent = "◈";

      const content = document.createElement("div");
      content.className = "info-content";

      const key = document.createElement("div");
      key.className = "info-key";
      key.textContent = fact.key;

      const value = document.createElement("div");
      value.className = "info-val";

      if (Array.isArray(fact.links) && fact.links.length > 0) {
        if (fact.value) {
          const summary = document.createElement("span");
          summary.textContent = `${fact.value} `;
          value.appendChild(summary);
        }

        fact.links.forEach((linkItem, linkIndex) => {
          const linked = document.createElement("a");
          linked.textContent = linkItem.label;
          safeExternalLink(linked, linkItem.href);
          value.appendChild(linked);

          if (linkIndex < fact.links.length - 1) {
            value.appendChild(document.createTextNode(" · "));
          }
        });
      } else if (/^\S+@\S+\.\S+$/.test(fact.value)) {
        const emailLink = document.createElement("a");
        emailLink.href = `mailto:${fact.value}`;
        emailLink.textContent = fact.value;
        value.appendChild(emailLink);
      } else if (fact.href) {
        const genericLink = document.createElement("a");
        genericLink.textContent = fact.value;
        safeExternalLink(genericLink, fact.href);
        value.appendChild(genericLink);
      } else {
        value.textContent = fact.value;
      }

      content.appendChild(key);
      content.appendChild(value);
      row.appendChild(icon);
      row.appendChild(content);
      factsWrap.appendChild(row);
    });
  }

  function renderResearch() {
    const researchWrap = byId("researchGrid");
    if (!researchWrap || !Array.isArray(data.research)) {
      return;
    }

    const icons = ["⬡", "⬢", "◇", "△", "○", "□"];

    data.research.forEach((item, index) => {
      const card = document.createElement("article");
      card.className = "research-card fade-in";
      card.style.transitionDelay = `${index * 0.1}s`;

      const icon = document.createElement("span");
      icon.className = "research-icon";
      icon.textContent = icons[index % icons.length];

      const title = document.createElement("h3");
      title.textContent = item.title;

      const desc = document.createElement("p");
      desc.textContent = item.description;

      card.appendChild(icon);
      card.appendChild(title);
      card.appendChild(desc);
      researchWrap.appendChild(card);
    });
  }

  function isOwnAuthor(author) {
    if (!author || !data.identity || !data.identity.name) {
      return false;
    }
    return author.toLowerCase() === data.identity.name.toLowerCase();
  }

  function appendAuthorList(container, authors) {
    if (!container || !Array.isArray(authors)) {
      return;
    }

    authors.forEach((author, index) => {
      if (isOwnAuthor(author)) {
        const strong = document.createElement("strong");
        strong.textContent = author;
        container.appendChild(strong);
      } else {
        container.appendChild(document.createTextNode(author));
      }

      if (index < authors.length - 1) {
        container.appendChild(document.createTextNode(", "));
      }
    });
  }

  function appendSourceLinks(container, sources, primaryUrl) {
    if (!Array.isArray(sources) || sources.length === 0) {
      return;
    }

    const primary = typeof primaryUrl === "string" ? primaryUrl.trim().toLowerCase() : "";
    const seen = new Set();
    const validSources = sources.filter((source) => {
      if (!source || !source.label || !source.href) {
        return false;
      }

      const href = source.href.trim();
      if (!href) {
        return false;
      }

      const normalized = href.toLowerCase();
      if (normalized === primary || seen.has(normalized)) {
        return false;
      }

      seen.add(normalized);
      return true;
    });

    if (validSources.length === 0) {
      return;
    }

    const sourceWrap = document.createElement("div");
    sourceWrap.className = "pub-sources";

    validSources.forEach((source, index) => {
      const link = document.createElement("a");
      link.textContent = source.label;
      safeExternalLink(link, source.href);
      sourceWrap.appendChild(link);

      if (index < validSources.length - 1) {
        sourceWrap.appendChild(document.createTextNode(" · "));
      }
    });

    container.appendChild(sourceWrap);
  }

  function renderPublications() {
    const publicationWrap = byId("publicationList");
    if (!publicationWrap || !Array.isArray(data.publications)) {
      return;
    }

    data.publications.forEach((publication, index) => {
      const card = document.createElement("article");
      card.className = "pub-card fade-in";
      card.style.transitionDelay = `${index * 0.05}s`;

      const meta = document.createElement("div");
      meta.className = "pub-meta";

      const venue = document.createElement("span");
      venue.className = "pub-venue";
      venue.textContent = publication.venue;

      const year = document.createElement("span");
      year.className = "pub-year";
      year.textContent = publication.year;

      meta.appendChild(venue);
      meta.appendChild(year);

      if (publication.status) {
        const badge = document.createElement("span");
        badge.className = "pub-badge";
        badge.textContent = publication.status;
        meta.appendChild(badge);
      }

      const title = document.createElement("div");
      title.className = "pub-title";
      if (publication.url) {
        const link = document.createElement("a");
        link.textContent = publication.title;
        safeExternalLink(link, publication.url);
        title.appendChild(link);
      } else {
        title.textContent = publication.title;
      }

      const authors = document.createElement("div");
      authors.className = "pub-authors";
      appendAuthorList(authors, publication.authors);

      card.appendChild(meta);
      card.appendChild(title);
      card.appendChild(authors);
      appendSourceLinks(card, publication.sources, publication.url);
      publicationWrap.appendChild(card);
    });
  }

  function renderPresentations() {
    const presentationWrap = byId("presentationList");
    if (!presentationWrap || !Array.isArray(data.presentations)) {
      return;
    }

    data.presentations.forEach((presentation, index) => {
      const card = document.createElement("article");
      card.className = "pub-card fade-in";
      card.style.transitionDelay = `${index * 0.05}s`;

      const meta = document.createElement("div");
      meta.className = "pub-meta";

      const event = document.createElement("span");
      event.className = "pub-venue";
      event.textContent = presentation.event;

      const year = document.createElement("span");
      year.className = "pub-year";
      year.textContent = presentation.year;

      meta.appendChild(event);
      meta.appendChild(year);

      if (presentation.type) {
        const badge = document.createElement("span");
        badge.className = "pub-badge";
        badge.textContent = presentation.type;
        meta.appendChild(badge);
      }

      const title = document.createElement("div");
      title.className = "pub-title";
      if (presentation.url) {
        const link = document.createElement("a");
        link.textContent = presentation.title;
        safeExternalLink(link, presentation.url);
        title.appendChild(link);
      } else {
        title.textContent = presentation.title;
      }

      card.appendChild(meta);
      card.appendChild(title);
      appendSourceLinks(card, presentation.sources, presentation.url);
      presentationWrap.appendChild(card);
    });
  }

  function renderExperience() {
    const timeline = byId("experienceTimeline");
    if (!timeline || !Array.isArray(data.experience)) {
      return;
    }

    data.experience.forEach((item) => {
      const card = document.createElement("article");
      card.className = "timeline-item";

      const header = document.createElement("div");
      header.className = "timeline-header";

      const role = document.createElement("span");
      role.className = "timeline-role";
      role.textContent = item.role;

      const date = document.createElement("span");
      date.className = "timeline-date";
      date.textContent = item.period;

      const org = document.createElement("div");
      org.className = "timeline-org";
      const orgParts = [item.organization, item.location].filter((value) => value);
      org.textContent = orgParts.join(" · ");

      const desc = document.createElement("div");
      desc.className = "timeline-desc";
      desc.textContent = item.highlights.join(" ");

      header.appendChild(role);
      header.appendChild(date);
      card.appendChild(header);
      card.appendChild(org);
      card.appendChild(desc);
      timeline.appendChild(card);
    });
  }

  function parseEducationDegree(degree) {
    const text = degree || "";
    if (text.toLowerCase().startsWith("phd")) {
      return {
        level: "Doctor of Philosophy",
        title: text.replace(/^phd\s+in\s+/i, "")
      };
    }
    if (text.toLowerCase().startsWith("msc")) {
      return {
        level: "Master of Science",
        title: text.replace(/^msc\s+in\s+/i, "")
      };
    }
    if (text.toLowerCase().startsWith("bsc")) {
      return {
        level: "Bachelor of Science",
        title: text.replace(/^bsc\s+in\s+/i, "")
      };
    }
    return {
      level: "Degree",
      title: text
    };
  }

  function renderEducation() {
    const educationWrap = byId("educationGrid");
    if (!educationWrap || !Array.isArray(data.education)) {
      return;
    }

    data.education.forEach((entry, index) => {
      const parsed = parseEducationDegree(entry.degree);

      const card = document.createElement("article");
      card.className = "edu-card fade-in";
      card.style.transitionDelay = `${index * 0.1}s`;

      const degree = document.createElement("div");
      degree.className = "edu-degree";
      degree.textContent = parsed.level;

      const title = document.createElement("h3");
      title.textContent = parsed.title;

      const school = document.createElement("div");
      school.className = "edu-school";
      school.textContent = entry.school;

      const years = document.createElement("div");
      years.className = "edu-years";
      years.textContent = entry.period;

      const note = document.createElement("div");
      note.className = "edu-note";
      note.textContent = entry.note;

      card.appendChild(degree);
      card.appendChild(title);
      card.appendChild(school);
      card.appendChild(years);
      card.appendChild(note);
      educationWrap.appendChild(card);
    });
  }

  function renderService() {
    const serviceWrap = byId("serviceGrid");
    if (!serviceWrap || !data.service) {
      return;
    }

    const groups = [
      { title: "Appointments", items: data.service.appointments || [] },
      { title: "Mentoring and Supervision", items: data.service.mentoringAndSupervision || [] },
      { title: "Reviewing and Organization", items: data.service.community || [] },
      { title: "Outreach and Grants", items: data.service.outreachAndGrants || [] }
    ];

    groups.forEach((group, index) => {
      const card = document.createElement("article");
      card.className = "research-card fade-in";
      card.style.transitionDelay = `${index * 0.08}s`;

      const title = document.createElement("h3");
      title.textContent = group.title;

      const list = document.createElement("ul");
      list.className = "service-list";

      group.items.forEach((item) => {
        const li = document.createElement("li");

        if (item && typeof item === "object" && !Array.isArray(item)) {
          if (Array.isArray(item.segments) && item.segments.length > 0) {
            item.segments.forEach((segment) => {
              if (typeof segment === "string") {
                li.appendChild(document.createTextNode(segment));
                return;
              }

              if (!segment || typeof segment !== "object" || !segment.href) {
                return;
              }

              const anchor = document.createElement("a");
              anchor.textContent = segment.label || segment.href;
              safeExternalLink(anchor, segment.href);
              li.appendChild(anchor);
            });
            list.appendChild(li);
            return;
          }

          if (typeof item.text === "string") {
            li.appendChild(document.createTextNode(item.text));
          }

          if (Array.isArray(item.links) && item.links.length > 0) {
            if (li.childNodes.length > 0) {
              li.appendChild(document.createTextNode(" "));
            }

            item.links.forEach((linkItem, linkIndex) => {
              if (!linkItem || !linkItem.href) {
                return;
              }

              const anchor = document.createElement("a");
              anchor.textContent = linkItem.label || linkItem.href;
              safeExternalLink(anchor, linkItem.href);
              li.appendChild(anchor);

              if (linkIndex < item.links.length - 1) {
                li.appendChild(document.createTextNode(" · "));
              }
            });
          }
        } else {
          li.textContent = item;
        }

        list.appendChild(li);
      });

      card.appendChild(title);
      card.appendChild(list);
      serviceWrap.appendChild(card);
    });
  }

  function initialsForLink(label) {
    const map = {
      github: "GH",
      linkedin: "in",
      "google scholar": "GS",
      openreview: "OR",
      orcid: "ID"
    };
    const key = label.toLowerCase();
    return map[key] || label.slice(0, 2).toUpperCase();
  }

  function renderContact() {
    const contactData = data.contact || {};
    const title = byId("contactTitle");
    const intro = byId("contactIntro");
    const email = byId("contactEmail");
    const links = byId("contactLinks");

    if (title) {
      title.textContent = contactData.title || "Contact";
    }

    if (intro) {
      intro.textContent = contactData.intro || "";
    }

    if (email) {
      if (contactData.email) {
        email.textContent = contactData.email;
        email.href = `mailto:${contactData.email}`;
        email.style.display = "inline-flex";
      } else {
        email.style.display = "none";
      }
    }

    if (!links || !Array.isArray(contactData.links)) {
      return;
    }

    links.textContent = "";

    contactData.links.forEach((item) => {
      const anchor = document.createElement("a");
      anchor.className = "social-link";
      safeExternalLink(anchor, item.href);

      const icon = document.createElement("div");
      icon.className = "social-icon";
      icon.textContent = initialsForLink(item.label);

      const info = document.createElement("div");
      info.className = "social-info";

      const name = document.createElement("div");
      name.className = "social-name";
      name.textContent = item.label;

      const handle = document.createElement("div");
      handle.className = "social-handle";
      handle.textContent = item.handle;

      const arrow = document.createElement("span");
      arrow.className = "social-arrow";
      arrow.textContent = "→";

      info.appendChild(name);
      info.appendChild(handle);
      anchor.appendChild(icon);
      anchor.appendChild(info);
      anchor.appendChild(arrow);
      links.appendChild(anchor);
    });
  }

  function renderFooter() {
    const footerData = data.footer || {};
    const year = byId("footerYear");
    const name = byId("footerName");
    const meta = byId("footerMeta");

    if (year) {
      year.textContent = `© ${new Date().getFullYear()}`;
    }

    if (name && data.identity) {
      name.textContent = data.identity.name;
    }

    if (meta) {
      const metaParts = [footerData.institution, footerData.location].filter((value) => value);
      meta.textContent = metaParts.join(" · ");
    }
  }

  function setupFadeIn() {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll(".fade-in").forEach((node) => observer.observe(node));
  }

  function setupMicroscopyCanvas() {
    const canvas = byId("microCanvas");
    const hero = byId("hero");
    if (!canvas || !hero) {
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    const cellTypes = [
      { color: "#5eead4", radius: [3, 6], count: 100, alpha: 0.82 },
      { color: "#818cf8", radius: [2, 5], count: 75, alpha: 0.78 },
      { color: "#f472b6", radius: [2, 4], count: 55, alpha: 0.72 },
      { color: "#fb923c", radius: [4, 7], count: 35, alpha: 0.68 },
      { color: "#94a3b8", radius: [2, 4], count: 65, alpha: 0.48 }
    ];

    const driftPreset = {
      connectionDistance: 32,
      maxConnectionsPerCell: 4,
      velocityJitter: 0.018,
      damping: 0.992,
      initialVelocity: 0.28,
      maxSpeedMin: 0.08,
      maxSpeedRange: 0.05
    };

    const connectionDistance = driftPreset.connectionDistance;
    const connectionDistanceSq = connectionDistance * connectionDistance;
    const maxConnectionsPerCell = driftPreset.maxConnectionsPerCell;

    let cells = [];
    let edges = [];
    let frame = 0;

    function gaussian() {
      let u = 0;
      let v = 0;
      while (u === 0) {
        u = Math.random();
      }
      while (v === 0) {
        v = Math.random();
      }
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    }

    function rebuildCells() {
      const width = canvas.width;
      const height = canvas.height;
      cells = [];
      edges = [];

      cellTypes.forEach((type, typeIndex) => {
        const clusterCount = 4 + Math.floor(Math.random() * 3);
        const centers = Array.from({ length: clusterCount }, () => ({
          x: 40 + Math.random() * (width - 80),
          y: 40 + Math.random() * (height - 80)
        }));

        for (let i = 0; i < type.count; i += 1) {
          const center = centers[Math.floor(Math.random() * centers.length)];
          const spread = 50 + Math.random() * 30;
          const x = center.x + gaussian() * spread;
          const y = center.y + gaussian() * spread;
          const radius = type.radius[0] + Math.random() * (type.radius[1] - type.radius[0]);

          cells.push({
            x: Math.max(radius, Math.min(width - radius, x)),
            y: Math.max(radius, Math.min(height - radius, y)),
            radius,
            color: type.color,
            alpha: type.alpha * (0.55 + Math.random() * 0.45),
            vx: (Math.random() - 0.5) * driftPreset.initialVelocity,
            vy: (Math.random() - 0.5) * driftPreset.initialVelocity,
            maxSpeed: driftPreset.maxSpeedMin + Math.random() * driftPreset.maxSpeedRange,
            typeIndex
          });
        }
      });
    }

    function updateCells(width, height) {
      cells.forEach((cell) => {
        // Add random drift so cells wander instead of oscillating around a fixed point.
        cell.vx += (Math.random() - 0.5) * driftPreset.velocityJitter;
        cell.vy += (Math.random() - 0.5) * driftPreset.velocityJitter;
        cell.vx *= driftPreset.damping;
        cell.vy *= driftPreset.damping;

        const speed = Math.hypot(cell.vx, cell.vy);
        if (speed > cell.maxSpeed) {
          const scale = cell.maxSpeed / speed;
          cell.vx *= scale;
          cell.vy *= scale;
        }

        cell.x += cell.vx;
        cell.y += cell.vy;

        if (cell.x < cell.radius) {
          cell.x = cell.radius;
          cell.vx = Math.abs(cell.vx);
        } else if (cell.x > width - cell.radius) {
          cell.x = width - cell.radius;
          cell.vx = -Math.abs(cell.vx);
        }

        if (cell.y < cell.radius) {
          cell.y = cell.radius;
          cell.vy = Math.abs(cell.vy);
        } else if (cell.y > height - cell.radius) {
          cell.y = height - cell.radius;
          cell.vy = -Math.abs(cell.vy);
        }
      });
    }

    function rebuildEdges() {
      edges = [];
      const buckets = new Map();
      const connections = new Array(cells.length).fill(0);

      cells.forEach((cell, index) => {
        const bx = Math.floor(cell.x / connectionDistance);
        const by = Math.floor(cell.y / connectionDistance);
        const key = `${bx},${by}`;

        if (!buckets.has(key)) {
          buckets.set(key, []);
        }
        buckets.get(key).push(index);
      });

      for (let i = 0; i < cells.length; i += 1) {
        if (connections[i] >= maxConnectionsPerCell) {
          continue;
        }

        const cell = cells[i];
        const bx = Math.floor(cell.x / connectionDistance);
        const by = Math.floor(cell.y / connectionDistance);

        for (let ox = -1; ox <= 1; ox += 1) {
          for (let oy = -1; oy <= 1; oy += 1) {
            const key = `${bx + ox},${by + oy}`;
            const nearby = buckets.get(key);
            if (!nearby) {
              continue;
            }

            for (const j of nearby) {
              if (j <= i) {
                continue;
              }

              if (connections[i] >= maxConnectionsPerCell || connections[j] >= maxConnectionsPerCell) {
                continue;
              }

              const other = cells[j];
              const dx = cell.x - other.x;
              const dy = cell.y - other.y;
              const distSq = dx * dx + dy * dy;

              if (distSq > connectionDistanceSq) {
                continue;
              }

              edges.push([i, j, distSq]);
              connections[i] += 1;
              connections[j] += 1;
            }
          }
        }
      }
    }

    function resize() {
      canvas.width = hero.offsetWidth;
      canvas.height = hero.offsetHeight;
      rebuildCells();
    }

    function drawFrame() {
      const width = canvas.width;
      const height = canvas.height;

      context.clearRect(0, 0, width, height);
      context.fillStyle = "#0c0f14";
      context.fillRect(0, 0, width, height);

      updateCells(width, height);
      rebuildEdges();

      for (let y = 0; y < height; y += 3) {
        context.fillStyle = "rgba(255,255,255,0.01)";
        context.fillRect(0, y, width, 1);
      }

      edges.forEach(([firstIndex, secondIndex, distSq]) => {
        const first = cells[firstIndex];
        const second = cells[secondIndex];

        const firstX = first.x;
        const firstY = first.y;
        const secondX = second.x;
        const secondY = second.y;

        const intensity = 1 - distSq / connectionDistanceSq;
        const alphaHex = Math.max(0, Math.min(255, Math.floor((0.04 + intensity * 0.18) * 255)))
          .toString(16)
          .padStart(2, "0");

        context.beginPath();
        context.moveTo(firstX, firstY);
        context.lineTo(secondX, secondY);
        context.strokeStyle = `${first.color}${alphaHex}`;
        context.lineWidth = 0.5;
        context.stroke();
      });

      cells.forEach((cell) => {
        const pointX = cell.x;
        const pointY = cell.y;

        context.beginPath();
        context.arc(pointX, pointY, cell.radius + 2, 0, Math.PI * 2);
        context.strokeStyle = `${cell.color}28`;
        context.lineWidth = 1;
        context.stroke();

        context.beginPath();
        context.arc(pointX + 0.5, pointY + 0.7, cell.radius * 0.55, 0, Math.PI * 2);
        context.fillStyle = "rgba(0,0,0,0.3)";
        context.fill();

        context.beginPath();
        context.arc(pointX, pointY, cell.radius, 0, Math.PI * 2);
        context.fillStyle = cell.color;
        context.globalAlpha = cell.alpha;
        context.fill();
        context.globalAlpha = 1;

        context.beginPath();
        context.arc(pointX - cell.radius * 0.2, pointY - cell.radius * 0.2, cell.radius * 0.42, 0, Math.PI * 2);
        context.fillStyle = "rgba(255,255,255,0.16)";
        context.fill();
      });

      const gradient = context.createLinearGradient(0, 0, width, 0);
      gradient.addColorStop(0, "rgba(12,15,20,0.82)");
      gradient.addColorStop(0.45, "rgba(12,15,20,0.55)");
      gradient.addColorStop(1, "rgba(12,15,20,0.15)");
      context.fillStyle = gradient;
      context.fillRect(0, 0, width, height);

      const vignette = context.createRadialGradient(width / 2, height / 2, width * 0.3, width / 2, height / 2, width * 0.75);
      vignette.addColorStop(0, "rgba(0,0,0,0)");
      vignette.addColorStop(1, "rgba(0,0,0,0.5)");
      context.fillStyle = vignette;
      context.fillRect(0, 0, width, height);
    }

    function stop() {
      if (frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    }

    function animate() {
      drawFrame();
      frame = requestAnimationFrame(animate);
    }

    function start() {
      stop();
      resize();
      if (prefersReducedMotion.matches) {
        drawFrame();
        return;
      }
      frame = requestAnimationFrame(animate);
    }

    window.addEventListener("resize", start);

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        stop();
      } else {
        start();
      }
    });

    if (typeof prefersReducedMotion.addEventListener === "function") {
      prefersReducedMotion.addEventListener("change", start);
    } else if (typeof prefersReducedMotion.addListener === "function") {
      prefersReducedMotion.addListener(start);
    }

    start();
  }

  setSeo();
  renderNavigation();
  renderHero();
  renderAbout();
  renderQuickFacts();
  renderResearch();
  renderPublications();
  renderPresentations();
  renderExperience();
  renderEducation();
  renderService();
  renderContact();
  renderFooter();
  setupFadeIn();
  setupMicroscopyCanvas();
})();
