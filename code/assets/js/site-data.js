window.siteData = {
  "seo": {
    "title": "Your Name | Professional Profile",
    "description": "Professional profile website for Your Name, generated from a LaTeX CV source."
  },
  "identity": {
    "name": "Your Name",
    "initials": "YN"
  },
  "navigation": [
    {
      "id": "about",
      "label": "About"
    },
    {
      "id": "research",
      "label": "Research"
    },
    {
      "id": "experience",
      "label": "Experience"
    },
    {
      "id": "education",
      "label": "Education"
    },
    {
      "id": "related-coursework",
      "label": "Related Coursework"
    },
    {
      "id": "service",
      "label": "Appointments and Outreach"
    },
    {
      "id": "research-and-summer-schools",
      "label": "Research and Summer Schools"
    },
    {
      "id": "workshops-and-conferences",
      "label": "Workshops and Conferences"
    },
    {
      "id": "trainings",
      "label": "Trainings"
    },
    {
      "id": "publications",
      "label": "Publications"
    },
    {
      "id": "presentations",
      "label": "Talks"
    },
    {
      "id": "computer-skills",
      "label": "Computer Skills"
    },
    {
      "id": "misc",
      "label": "Misc"
    },
    {
      "id": "contact",
      "label": "Contact"
    }
  ],
  "hero": {
    "eyebrow": "Position at Company | City, Country",
    "role": "Position at Company",
    "summary": "Details: Some description.",
    "actions": [
      {
        "label": "Email",
        "href": "mailto:your.email@university.edu",
        "style": "primary"
      }
    ]
  },
  "quickFacts": [
    {
      "key": "Current Role",
      "value": "Position at Company"
    },
    {
      "key": "Primary Organization",
      "value": "Company"
    },
    {
      "key": "Latest Degree",
      "value": "Degree"
    },
    {
      "key": "Location",
      "value": "City, Country"
    },
    {
      "key": "Email",
      "value": "your.email@university.edu"
    },
    {
      "key": "Phone",
      "value": "Your phone number"
    }
  ],
  "about": {
    "paragraphs": [
      "Your Name currently works as Position at Company.",
      "Recent experience includes work at Company."
    ],
    "skills": [
      "Basic",
      "LaTeX"
    ]
  },
  "research": [
    {
      "title": "Details: Some description",
      "description": "Published at Affiliation (Dates)."
    },
    {
      "title": "Position at Company",
      "description": "Details: Some description."
    }
  ],
  "publications": [
    {
      "title": "Details: Some description",
      "venue": "Affiliation",
      "year": "Dates",
      "status": "Conference",
      "authors": [
        "Authors"
      ],
      "url": ""
    }
  ],
  "presentations": [
    {
      "title": "Details: Some description",
      "event": "Company/Institution",
      "year": "Dates",
      "type": "Position",
      "url": ""
    },
    {
      "title": "Details: Some description",
      "event": "Affiliation",
      "year": "Dates",
      "type": "Poster",
      "url": ""
    }
  ],
  "experience": [
    {
      "role": "Position",
      "organization": "Company",
      "location": "",
      "period": "Dates",
      "highlights": [
        "Details: Some description"
      ]
    }
  ],
  "education": [
    {
      "degree": "Degree",
      "school": "University",
      "period": "Dates",
      "note": "Details: Some description"
    }
  ],
  "service": {
    "appointments": [
      "Company/Institution (Dates): Details: Some description."
    ],
    "mentoringAndSupervision": [],
    "community": [
      "Reviewing Experience (Dates): Details: Some description.",
      "Conference and Seminar Organization (Dates): Details: Some description.",
      "Recruitment Committees (Dates): Details: Some description.",
      "Session Chairing and Panel Moderation (Dates): Details: Some description.",
      "Company/Institution - Position (Dates): Details: Some description."
    ],
    "outreachAndGrants": [
      "Event - Organization (Dates): Details: Some description.",
      "Name - Company/Institution (Dates): Details: Some description."
    ]
  },
  "customSections": [
    {
      "id": "related-coursework",
      "title": "Related Coursework",
      "items": [
        "Course - Institution: Details: Some description."
      ]
    },
    {
      "id": "research-and-summer-schools",
      "title": "Research and Summer Schools",
      "items": [
        "Institution - location (Dates): Details: Some description."
      ]
    },
    {
      "id": "workshops-and-conferences",
      "title": "Workshops and Conferences",
      "items": [
        "Company/Institution - Position (dates): Details: Some description."
      ]
    },
    {
      "id": "trainings",
      "title": "Trainings",
      "items": [
        "Company/Institution - Position (Dates): Details: Some description."
      ]
    },
    {
      "id": "computer-skills",
      "title": "Computer Skills",
      "items": [
        "Compiled languages: Basic.",
        "Scientific software: Intermediate.",
        "Scientific software: Basic.",
        "Markup languages: Advanced: LaTeX.",
        "Markup languages: Basic."
      ]
    },
    {
      "id": "misc",
      "title": "Misc",
      "items": [
        "Languages: Arabic.",
        "Languages: English.",
        "Languages: French.",
        "Languages: German.",
        "Languages: Polish.",
        "Languages: Russian.",
        "Languages: Swedish.",
        "Languages: Spanish."
      ]
    }
  ],
  "contact": {
    "title": "Open to collaboration opportunities.",
    "intro": "Use the contact methods below to get in touch.",
    "email": "your.email@university.edu",
    "links": []
  },
  "footer": {
    "institution": "Company",
    "location": "City, Country"
  }
};

(function () {
    if (typeof window === "undefined" || typeof document === "undefined") {
        return;
    }

    function getData() {
        return window.siteData || window.testSiteData || null;
    }

    function ensureNavLinks(customSections) {
        var navList = document.getElementById("navList");
        if (!navList) {
            return;
        }

        customSections.forEach(function (section) {
            if (!section || !section.id) {
                return;
            }

            if (navList.querySelector('a[href="#' + section.id + '"]')) {
                return;
            }

            var li = document.createElement("li");
            var a = document.createElement("a");
            a.href = "#" + section.id;
            a.textContent = section.title || section.id;
            li.appendChild(a);
            navList.appendChild(li);
        });
    }

    function buildSectionNode(section) {
        var node = document.createElement("section");
        node.id = section.id;

        var container = document.createElement("div");
        container.className = "container";

        var header = document.createElement("div");
        header.className = "section-header";

        var number = document.createElement("div");
        number.className = "section-num";
        number.textContent = "00";

        var heading = document.createElement("h2");
        heading.textContent = section.title || section.id;

        var line = document.createElement("div");
        line.className = "section-line";

        header.appendChild(number);
        header.appendChild(heading);
        header.appendChild(line);

        var card = document.createElement("article");
        card.className = "research-card fade-in visible";

        var list = document.createElement("ul");
        list.className = "service-list";

        var items = Array.isArray(section.items) ? section.items : [];
        items.forEach(function (itemText) {
            var li = document.createElement("li");
            li.textContent = itemText;
            list.appendChild(li);
        });

        if (!items.length) {
            var li = document.createElement("li");
            li.textContent = "No content extracted for this section yet.";
            list.appendChild(li);
        }

        card.appendChild(list);
        container.appendChild(header);
        container.appendChild(card);
        node.appendChild(container);
        return node;
    }

    function getDesiredOrder(data) {
        var ordered = ["hero"];
        var nav = Array.isArray(data && data.navigation) ? data.navigation : [];

        nav.forEach(function (item) {
            if (item && item.id) {
                ordered.push(item.id);
            }
        });

        var deduped = [];
        ordered.forEach(function (id) {
            if (deduped.indexOf(id) === -1) {
                deduped.push(id);
            }
        });

        return deduped;
    }

    function appendMissingCustomSections(data) {
        if (!Array.isArray(data.customSections) || !data.customSections.length) {
            return;
        }

        var footer = document.querySelector("footer");
        var body = document.body;

        data.customSections.forEach(function (section) {
            if (!section || !section.id) {
                return;
            }

            if (document.getElementById(section.id)) {
                return;
            }

            var node = buildSectionNode(section);
            if (footer) {
                body.insertBefore(node, footer);
            } else {
                body.appendChild(node);
            }
        });
    }

    function reorderSections(data) {
        var footer = document.querySelector("footer");
        var body = document.body;
        var desiredOrder = getDesiredOrder(data);

        desiredOrder.forEach(function (sectionId) {
            var section = document.getElementById(sectionId);
            if (!section || section.tagName.toLowerCase() !== "section") {
                return;
            }

            if (footer) {
                body.insertBefore(section, footer);
            } else {
                body.appendChild(section);
            }
        });

        var counter = 1;
        desiredOrder.forEach(function (sectionId) {
            if (sectionId === "hero") {
                return;
            }

            var section = document.getElementById(sectionId);
            if (!section || section.tagName.toLowerCase() !== "section") {
                return;
            }

            var num = section.querySelector(".section-num");
            if (num) {
                num.textContent = String(counter).padStart(2, "0");
            }
            counter += 1;
        });
    }

    function renderCustomSections() {
        var data = getData();
        if (!data) {
            return;
        }

        if (Array.isArray(data.customSections) && data.customSections.length) {
            ensureNavLinks(data.customSections);
            appendMissingCustomSections(data);
        }

        reorderSections(data);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            setTimeout(renderCustomSections, 0);
        });
    } else {
        setTimeout(renderCustomSections, 0);
    }
})();
