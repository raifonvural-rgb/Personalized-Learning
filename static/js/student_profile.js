"use strict";

/* ========================================
   ÖĞRENCİ PROFİLİ YÖNETİM MOTORU
   ======================================== */

document.addEventListener("DOMContentLoaded", () => {

    const byId = id => document.getElementById(id);

    const dialog = byId("student-profile-dialog");
    const studentSelect = byId("profile-student-select");
    const openButton = byId("profile-open-button");
    const form = byId("student-profile-form");

    if (!dialog || !studentSelect || !form) {
        return;
    }

    const navigation = byId("profile-section-navigation");
    const fieldsContainer = byId("profile-fields");
    const saveButton = byId("profile-save-button");
    const saveStatus = byId("profile-save-status");
    const selectionStatus = byId("profile-selection-status");

    const apiBase = dialog.dataset.apiBase ||
                    "/api/student-profiles";

    let schema = [];
    let profile = null;
    let activeSection = 0;
    let savedSnapshot = "";
    let busy = false;
    let selectedStudentId = "";
    let fieldCounter = 0;


    /* ========================================
       1. BÖLÜM AÇIKLAMALARI
       ======================================== */

    const descriptions = {
        general:
            "Öğrencinin genel özelliklerini ve öğretmen gözlemlerini tanımlayın.",

        visual:
            "Materyallerin görsel tasarımını etkileyen özellikleri tanımlayın.",

        auditory:
            "Sesli yönergeler, ses tercihleri ve işitsel hassasiyetleri tanımlayın.",

        motor:
            "Öğrencinin fiziksel etkileşim ve motor becerilerini tanımlayın.",

        communication:
            "Dil, iletişim ve yönergeleri anlama özelliklerini tanımlayın.",

        learning:
            "Dikkat, öğrenme süresi ve destek gereksinimlerini tanımlayın.",

        motivation:
            "Öğrenciye uygun motivasyon ve geri bildirim yöntemlerini tanımlayın.",

        sensory_emotional:
            "Duyusal hassasiyetleri ve duygusal destek gereksinimlerini tanımlayın.",

        academic:
            "Öğrencinin mevcut akademik becerilerini ve öğrenme hedeflerini tanımlayın.",

        custom_requirements:
            "Hazır alanlarda bulunmayan öğrenciye özgü gereksinimleri tanımlayın."
    };

    const icons = {
        general: "01",
        visual: "02",
        auditory: "03",
        motor: "04",
        communication: "05",
        learning: "06",
        motivation: "07",
        sensory_emotional: "08",
        academic: "09",
        custom_requirements: "10"
    };


    /* ========================================
       2. YARDIMCI FONKSİYONLAR
       ======================================== */

    function element(tag, className, text) {

        const node = document.createElement(tag);

        if (className) {
            node.className = className;
        }

        if (text !== undefined) {
            node.textContent = text;
        }

        return node;
    }

    function emptyValue(field) {

        if (field.type === "multiselect") {
            return [];
        }

        if (field.type === "number") {
            return null;
        }

        return "";
    }

    function setStatus(node, message = "", type = "") {

        node.textContent = message;
        node.classList.remove("error", "success");

        if (type) {
            node.classList.add(type);
        }
    }

    function setBusy(value) {

        busy = value;

        saveButton.disabled = value;
        openButton.disabled = value;
        studentSelect.disabled = value;

        byId("profile-close-button").disabled = value;
        byId("profile-cancel-button").disabled = value;

        dialog.setAttribute("aria-busy", String(value));

        if (navigation) {
            navigation.inert = value;
        }

        if (fieldsContainer) {
            fieldsContainer.inert = value;
        }
    }

    function hasUnsavedChanges() {

        return profile !== null &&
            JSON.stringify(profile) !== savedSnapshot;
    }

    async function apiRequest(path = "", options = {}) {

        const response = await fetch(
            apiBase + path,
            {
                ...options,
                headers: {
                    "Accept": "application/json",
                    ...(options.headers || {})
                }
            }
        );

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error(
                "Sunucudan geçerli bir yanıt alınamadı."
            );
        }

        if (!response.ok) {
            throw new Error(
                data.error ||
                `Sunucu hatası (${response.status})`
            );
        }

        return data;
    }


    /* ========================================
       3. MERKEZİ ŞEMA VE ÖĞRENCİ LİSTESİ
       ======================================== */

    async function loadSchema() {

        if (schema.length > 0) {
            return;
        }

        const result = await apiRequest("/schema");

        if (!Array.isArray(result.schema)) {
            throw new Error("Profil şeması yüklenemedi.");
        }

        schema = result.schema;
    }

    async function refreshStudentList(
        preferredId = selectedStudentId
    ) {

        const result = await apiRequest();

        studentSelect.replaceChildren();

        const newOption = element(
            "option", "", "Yeni Öğrenci"
        );

        newOption.value = "";

        studentSelect.appendChild(newOption);

        for (const student of result.students) {

            const option = element(
                "option", "", student.name
            );

            option.value = student.id;

            studentSelect.appendChild(option);
        }

        const exists = Array.from(
            studentSelect.options
        ).some(option => option.value === preferredId);

        selectedStudentId = exists ? preferredId : "";

        studentSelect.value = selectedStudentId;
    }


    /* ========================================
       4. BOŞ PROFİL OLUŞTURMA
       ======================================== */

    function createEmptyProfile() {

        const result = {};

        for (const section of schema) {

            if (section.repeatable) {

                result[section.key] = [];

                continue;
            }

            result[section.key] = {};

            for (const field of section.fields) {

                result[section.key][field.key] =
                    emptyValue(field);
            }
        }

        return result;
    }


    /* ========================================
       5. PROFİL PENCERESİNİ AÇMA
       ======================================== */

    async function openProfile(studentId = "") {

        if (busy || dialog.open) {
            return;
        }

        setBusy(true);
        setStatus(selectionStatus);

        try {

            await loadSchema();

            if (studentId) {

                const result = await apiRequest(
                    "/" + encodeURIComponent(studentId)
                );

                profile = result.profile;

            } else {

                profile = createEmptyProfile();
            }

            activeSection = 0;

            savedSnapshot = JSON.stringify(profile);

            updateSubtitle();

            setStatus(saveStatus);

            renderNavigation();
            renderActiveSection();

            dialog.showModal();

        } catch (error) {

            setStatus(
                selectionStatus,
                error.message,
                "error"
            );

            studentSelect.value = selectedStudentId;

        } finally {

            setBusy(false);
        }
    }

    function updateSubtitle() {

        const name = profile?.general?.name?.trim();

        byId("profile-dialog-subtitle").textContent =
            name || "Yeni Öğrenci";
    }


    /* ========================================
       6. BÖLÜM GEZİNME MENÜSÜ
       ======================================== */

    function renderNavigation() {

        navigation.replaceChildren();

        schema.forEach((section, index) => {

            const button = element(
                "button",
                "profile-nav-button"
            );

            button.type = "button";

            if (index === activeSection) {

                button.classList.add("active");

                button.setAttribute(
                    "aria-current", "true"
                );
            }

            const icon = element(
                "span",
                "profile-nav-icon",
                String(index + 1).padStart(2, '0')
            );

            icon.setAttribute("aria-hidden", "true");

            const label = element(
                "span",
                "profile-nav-label",
                section.title
            );

            button.append(icon, label);

            button.addEventListener("click", () => {

                activeSection = index;

                renderNavigation();
                renderActiveSection();
            });

            navigation.appendChild(button);
        });
    }


    /* ========================================
       7. DİNAMİK FORM ALANLARI
       ======================================== */

    function renderField(field, target) {

        const wrapper = element(
            "div",
            "profile-field"
        );

        const id = "profile-field-" + (++fieldCounter);

        if (
            field.type === "textarea" ||
            field.type === "multiselect" ||
            field.type === "color"
        ) {
            wrapper.classList.add("full-width");
        }

        const label = element(
            field.type === "multiselect" ? "span" : "label",
            "profile-field-label",
            field.label
        );

        label.id = id + "-label";

        if (field.type !== "multiselect") {
            label.htmlFor = id;
        }

        if (field.required) {

            const marker = element(
                "span",
                "profile-required-marker",
                " *"
            );

            label.appendChild(marker);
        }

        wrapper.appendChild(label);

        const value = target[field.key] ??
                      emptyValue(field);

        let control;


        /* Çok satırlı metin */

        if (field.type === "textarea") {

            control = element("textarea");

            control.rows = 3;
            control.placeholder = "Belirtilmedi";
            control.value = value;

            control.addEventListener("input", () => {

                target[field.key] = control.value;
            });


        /* Açılır seçim menüsü */

        } else if (field.type === "select") {

            control = element("select");

            const placeholder = element(
                "option", "", "Belirtilmedi"
            );

            placeholder.value = "";

            control.appendChild(placeholder);

            for (const optionValue of field.options) {

                const option = element(
                    "option", "", optionValue
                );

                option.value = optionValue;

                control.appendChild(option);
            }

            control.value = value;

            control.addEventListener("change", () => {

                target[field.key] = control.value;
            });


        /* Çoklu seçim */

        } else if (field.type === "multiselect") {

            control = element(
                "div",
                "profile-checkbox-group"
            );

            control.setAttribute("role", "group");

            control.setAttribute(
                "aria-labelledby",
                label.id
            );

            for (const optionValue of field.options) {

                const optionLabel = element(
                    "label",
                    "profile-checkbox-option"
                );

                const checkbox = element("input");

                checkbox.type = "checkbox";

                checkbox.value = optionValue;

                checkbox.checked =
                    Array.isArray(value) &&
                    value.includes(optionValue);

                checkbox.addEventListener(
                    "change", () => {

                        target[field.key] = Array.from(
                            control.querySelectorAll(
                                "input:checked"
                            )
                        ).map(input => input.value);
                    }
                );

                optionLabel.append(
                    checkbox,
                    document.createTextNode(optionValue)
                );

                control.appendChild(optionLabel);
            }


        /* Sayısal alan */

        } else if (field.type === "number") {

            control = element("input");

            control.type = "number";
            control.min = "0";
            control.step = "any";
            control.placeholder = "Belirtilmedi";
            control.value = value ?? "";

            control.addEventListener("input", () => {

                target[field.key] = control.value === ""
                    ? null
                    : control.valueAsNumber;
            });


        /* Renk seçimi */

        } else if (field.type === "color") {

            const row = element(
                "div", "profile-color-row"
            );

            const picker = element("input");

            picker.type = "color";
            picker.id = id;

            const validColor =
                /^#[0-9a-f]{6}$/i.test(value);

            picker.value = validColor
                ? value
                : "#ffffff";

            const enabled = element("input");
            enabled.type = "checkbox";
            enabled.checked = validColor;

            const enabledLabel = element(
                "label",
                "profile-checkbox-option"
            );

            enabledLabel.append(
                enabled,
                document.createTextNode("Renk belirt")
            );

            picker.disabled = !enabled.checked;

            const colorText = element(
                "span",
                "profile-field-help",
                validColor ? value : "Belirtilmedi"
            );

            function updateColor() {

                picker.disabled = !enabled.checked;

                target[field.key] = enabled.checked
                    ? picker.value
                    : "";

                colorText.textContent =
                    target[field.key] ||
                    "Belirtilmedi";
            }

            enabled.addEventListener(
                "change", updateColor
            );

            picker.addEventListener(
                "input", updateColor
            );

            row.append(
                picker, enabledLabel, colorText
            );

            wrapper.appendChild(row);

            return wrapper;


        /* Standart metin alanı */

        } else {

            control = element("input");

            control.type = "text";
            control.placeholder = "Belirtilmedi";
            control.value = value;

            control.addEventListener("input", () => {

                target[field.key] = control.value;

                if (
                    activeSection === 0 &&
                    field.key === "name"
                ) {
                    updateSubtitle();
                }
            });
        }

        control.id = id;

        if (field.required) {
            control.required = true;
        }

        wrapper.appendChild(control);

        return wrapper;
    }


    /* ========================================
       8. SEÇİLEN BÖLÜMÜ GÖSTERME
       ======================================== */

    function renderActiveSection() {

        const section = schema[activeSection];

        if (!section || !profile) {
            return;
        }

        byId("profile-section-counter").textContent =
            `Bölüm ${activeSection + 1} / ${schema.length}`;

        byId("profile-section-title").textContent =
            section.title;

        byId("profile-section-description").textContent =
            descriptions[section.key] || "";

        fieldsContainer.replaceChildren();

        fieldCounter = 0;

        if (section.repeatable) {

            renderCustomRequirements(section);

        } else {

            if (!profile[section.key]) {
                profile[section.key] = {};
            }

            const target = profile[section.key];

            for (const field of section.fields) {

                fieldsContainer.appendChild(
                    renderField(field, target)
                );
            }
        }

        document.querySelector(
            ".profile-content"
        ).scrollTop = 0;
    }


    /* ========================================
       9. EK BİREYSEL GEREKSİNİMLER
       ======================================== */

    function renderCustomRequirements(section) {

        const key = section.key;

        if (!Array.isArray(profile[key])) {
            profile[key] = [];
        }

        const requirements = profile[key];

        const container = element(
            "div", "profile-requirements"
        );

        if (requirements.length === 0) {

            container.appendChild(
                element(
                    "div",
                    "profile-empty-message",
                    "Henüz ek bireysel gereksinim tanımlanmadı."
                )
            );
        }

        requirements.forEach((requirement, index) => {

            const card = element(
                "article",
                "profile-requirement-card"
            );

            const header = element(
                "div",
                "profile-requirement-header"
            );

            const title = element(
                "strong", "",
                `Gereksinim ${index + 1}`
            );

            const removeButton = element(
                "button",
                "profile-remove-button",
                "Gereksinimi Sil"
            );

            removeButton.type = "button";

            removeButton.addEventListener("click", () => {

                if (!window.confirm(
                    "Bu gereksinim silinsin mi?"
                )) {
                    return;
                }

                requirements.splice(index, 1);

                renderActiveSection();
            });

            header.append(title, removeButton);

            const fields = element(
                "div",
                "profile-requirement-fields"
            );

            for (const field of section.fields) {

                fields.appendChild(
                    renderField(field, requirement)
                );
            }

            card.append(header, fields);

            container.appendChild(card);
        });

        const addButton = element(
            "button",
            "profile-add-button",
            "+ Yeni Bireysel Gereksinim Ekle"
        );

        addButton.type = "button";

        addButton.addEventListener("click", () => {

            const requirement = {};

            for (const field of section.fields) {

                requirement[field.key] =
                    emptyValue(field);
            }

            requirements.push(requirement);

            renderActiveSection();

            const cards =
                fieldsContainer.querySelectorAll(
                    ".profile-requirement-card"
                );

            const lastCard = cards[cards.length - 1];

            if (lastCard) {

                lastCard.scrollIntoView({
                    block: "nearest"
                });

                lastCard.querySelector("input")?.focus();
            }
        });

        container.appendChild(addButton);

        fieldsContainer.appendChild(container);
    }


    /* ========================================
       10. KAYIT ÖNCESİ DOĞRULAMA
       ======================================== */

    function validateBeforeSave() {

        if (!profile.general?.name?.trim()) {

            activeSection = 0;

            renderNavigation();
            renderActiveSection();

            fieldsContainer.querySelector("input")?.focus();

            throw new Error(
                "Öğrencinin adı ve soyadı zorunludur."
            );
        }

        for (const section of schema) {

            const values = section.repeatable
                ? profile[section.key] || []
                : [profile[section.key] || {}];

            for (const entry of values) {

                for (const field of section.fields) {

                    const value = entry[field.key];

                    if (
                        field.type === "number" &&
                        value !== null &&
                        value !== "" &&
                        value !== undefined &&
                        (!Number.isFinite(value) || value < 0)
                    ) {

                        throw new Error(
                            `${section.title}: ${field.label} için geçersiz sayı.`
                        );
                    }
                }
            }
        }

        const requirements =
            profile.custom_requirements || [];

        for (let index = 0;
             index < requirements.length;
             index++) {

            const requirement = requirements[index];

            if (
                !requirement.name?.trim() ||
                !requirement.description?.trim() ||
                !requirement.priority
            ) {

                activeSection = schema.findIndex(
                    section =>
                        section.key === "custom_requirements"
                );

                renderNavigation();
                renderActiveSection();

                throw new Error(
                    `Gereksinim ${index + 1}: ` +
                    "Ad, açıklama ve öncelik belirtilmelidir."
                );
            }
        }
    }


    /* ========================================
       11. PROFİLİ KAYDETME
       ======================================== */

    async function saveProfile(event) {

        event.preventDefault();

        if (busy || !profile) {
            return;
        }

        setStatus(saveStatus);

        try {

            validateBeforeSave();

        } catch (error) {

            setStatus(
                saveStatus, error.message, "error"
            );

            return;
        }

        setBusy(true);

        setStatus(saveStatus, "Profil kaydediliyor...");

        let savedSuccessfully = false;

        try {

            const result = await apiRequest(
                "/save",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(profile)
                }
            );

            profile = result.profile;

            savedSnapshot = JSON.stringify(profile);

            selectedStudentId = profile.id;

            savedSuccessfully = true;

            await refreshStudentList(profile.id);

            const activeResponse = await fetch("/api/active-student", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    student_id: profile.id
                })
            });

            if (!activeResponse.ok) {
                throw new Error(
                    "Profil kaydedildi ancak aktif öğrenci güncellenemedi."
                );
            }

            const activeResult = await activeResponse.json();

            if (activeResult.student?.id !== profile.id) {
                throw new Error(
                    "Profil kaydedildi ancak aktif öğrenci doğrulanamadı."
                );
            }

            dialog.close();

            setStatus(
                selectionStatus,
                `${profile.general.name} — Profil kaydedildi ve öğrenci aktif yapıldı.`,
                "success"
            );

        } catch (error) {

            if (savedSuccessfully) {

                updateSubtitle();

                renderNavigation();
                renderActiveSection();

                setStatus(
                    saveStatus,
                    "Profil kaydedildi ancak işlem tamamlanamadı. " +
                    error.message,
                    "error"
                );

            } else {

                setStatus(
                    saveStatus,
                    error.message,
                    "error"
                );
            }

        } finally {

            setBusy(false);
        }
    }


    /* ========================================
       12. PENCEREYİ KAPATMA
       ======================================== */

    function requestClose() {

        if (busy) {
            return;
        }

        if (hasUnsavedChanges()) {

            const confirmed = window.confirm(
                "Kaydedilmemiş değişiklikler var. " +
                "Kaydetmeden çıkmak istiyor musunuz?"
            );

            if (!confirmed) {
                return;
            }
        }

        studentSelect.value = selectedStudentId;

        dialog.close();

        profile = null;
    }


    /* ========================================
       13. OLAY BAĞLANTILARI
       ======================================== */

    studentSelect.addEventListener("change", async () => {

        if (busy) return;

        const previousId = selectedStudentId;
        const requestedId = studentSelect.value;

        setBusy(true);

        try {
            const response = await fetch("/api/active-student", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({student_id: requestedId})
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Öğrenci seçilemedi.");
            }

            selectedStudentId = result.student?.id || "";

            setStatus(
                selectionStatus,
                result.student
                    ? "Aktif öğrenci: " + result.student.name
                    : "Henüz bir öğrenci seçilmedi.",
                result.student ? "success" : ""
            );

        } catch (error) {
            selectedStudentId = previousId;
            studentSelect.value = previousId;
            setStatus(selectionStatus, error.message, "error");
        } finally {
            setBusy(false);
        }
    });

    openButton.addEventListener("click", () => {

        openProfile(studentSelect.value);
    });

    byId("profile-close-button").addEventListener(
        "click", requestClose
    );

    byId("profile-cancel-button").addEventListener(
        "click", requestClose
    );

    dialog.addEventListener("cancel", event => {

        event.preventDefault();

        requestClose();
    });

    form.addEventListener("submit", saveProfile);

    window.addEventListener("beforeunload", event => {

        if (dialog.open && hasUnsavedChanges()) {

            event.preventDefault();

            event.returnValue = "";
        }
    });


    /* ========================================
       14. BAŞLANGIÇ
       ======================================== */

    async function initialize() {

        setBusy(true);

        try {

            await loadSchema();

            const response = await fetch("/api/active-student", {
                headers: {"Accept": "application/json"}
            });

            if (!response.ok) {
                throw new Error("Aktif öğrenci yüklenemedi.");
            }

            const result = await response.json();

            await refreshStudentList(result.student?.id || "");

            if (result.student && selectedStudentId) {
                setStatus(
                    selectionStatus,
                    "Aktif öğrenci: " + result.student.name,
                    "success"
                );
            }

        } catch (error) {

            setStatus(
                selectionStatus,
                error.message,
                "error"
            );

        } finally {

            setBusy(false);
        }
    }

    initialize();

});
