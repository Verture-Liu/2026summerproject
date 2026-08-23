let taskId = null;
let workflow = null;
let workflowValid = false;
let outputDirectorySelected = false;
let currentLanguage = "en";
let configurationReady = false;
let apiKeyPresent = false;
let hasFiles = false;
let configStatusKey = "";
let aboutData = null;
let sessionToken = "";
let reportObjectUrl = null;

const consumeSessionToken = () => {
  const fragment = window.location.hash;
  if (!fragment.startsWith("#token=")) return;
  try {
    sessionToken = decodeURIComponent(fragment.slice("#token=".length));
  } catch (_error) {
    sessionToken = "";
  } finally {
    history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
  }
};

consumeSessionToken();

const $ = (id) => document.getElementById(id);
const apiFetch = (path, options = {}) => fetch(path, {
  ...options,
  headers: {...options.headers, "X-PaleoRigor-Token": sessionToken}
});
const translations = {
  en: {
    eyebrow: "LOCAL RESEARCH AGENT",
    heroTitle: "Turn research requests into reviewable, reproducible local workflows",
    heroSubtitle: "The model API plans the workflow. Skills on your computer process the data.",
    heroCardTitle: "Local-first execution",
    heroCardText: "Files stay on this computer. You review every workflow before it runs.",
    stepApi: "Model API",
    stepUpload: "Upload files",
    stepPlan: "Plan workflow",
    stepOutput: "Choose output",
    stepRun: "Run locally",
    configurationTitle: "API Configuration",
    configurationHelp: "Save the API endpoint, model, and key securely before planning a workflow.",
    baseUrl: "Base URL",
    baseUrlPlaceholder: "https://api.example.com/v1",
    model: "Model",
    modelPlaceholder: "Model name",
    apiKey: "API Key",
    apiKeyPlaceholder: "Saved securely and never shown again",
    saveConfiguration: "Save Configuration",
    testConnection: "Test Connection",
    configurationSaved: "Configuration saved.",
    connectionPassed: "Connection passed.",
    invalidCredentials: "Invalid API credentials.",
    apiUnreachable: "The API could not be reached.",
    configurationMissing: "Complete and test the API configuration before planning a workflow.",
    configurationUnavailable: "Configuration is unavailable. Try again.",
    connectionFailed: "The connection test failed. Check the API configuration.",
    aboutTitle: "Included Tools",
    toolName: "Tool",
    toolVersion: "Pinned version",
    taskTitle: "Task and Files",
    taskHelp: "Describe the research task and upload the files that should be processed locally.",
    instructionPlaceholder: "Example: Keep peptide sequences between 13 and 26 amino acids and export a FASTA file.",
    uploadButton: "Create Task and Upload",
    planTitle: "Generate and Validate Workflow",
    planHelp: "The model drafts a workflow. The local app validates skill names, inputs, and outputs before execution.",
    planButton: "Generate Workflow",
    workflowEmpty: "No workflow generated yet.",
    runTitle: "Local Execution",
    runHelp: "Select where results should be copied, review the workflow, then run the local skills.",
    selectOutputButton: "Select Results Folder",
    outputEmpty: "No results folder selected.",
    approvalText: "I reviewed the workflow and approve running these Skills locally.",
    executeButton: "Run Workflow",
    runEmpty: "Waiting to run.",
    reportLink: "Open Run Report",
    working: "Working...",
    uploading: "Uploading files...",
    planning: "Planning workflow...",
    waitingFolder: "Waiting for folder selection...",
    running: "Running workflow locally...",
    openingPicker: "Opening the system folder picker...",
    workflowPlanningFailed: "Workflow planning failed.",
    validationPassed: "Validation passed.",
    validationReview: "Validation needs review.",
    localRunning: "Local execution is running. Some tools may take several minutes. Please keep this page open.",
  },
  zh: {
    eyebrow: "本地科研 AGENT",
    heroTitle: "把科研需求转换为可审核、可复现的本地工作流",
    heroSubtitle: "模型 API 负责规划 workflow；你电脑上的 Skills 负责处理数据。",
    heroCardTitle: "本地优先执行",
    heroCardText: "文件保留在本机。每个 workflow 都需要你审核后才会运行。",
    stepApi: "模型 API",
    stepUpload: "上传文件",
    stepPlan: "生成 workflow",
    stepOutput: "选择结果文件夹",
    stepRun: "本地运行",
    configurationTitle: "API 配置",
    configurationHelp: "请先安全保存 API 地址、模型和密钥，再生成 workflow。",
    baseUrl: "Base URL",
    baseUrlPlaceholder: "https://api.example.com/v1",
    model: "模型",
    modelPlaceholder: "模型名称",
    apiKey: "API Key",
    apiKeyPlaceholder: "安全保存，且不会再次显示",
    saveConfiguration: "保存配置",
    testConnection: "测试连接",
    configurationSaved: "配置已保存。",
    connectionPassed: "连接测试通过。",
    invalidCredentials: "API 凭据无效。",
    apiUnreachable: "无法连接 API。",
    configurationMissing: "请先完成并测试 API 配置，再生成 workflow。",
    configurationUnavailable: "配置暂时不可用，请重试。",
    connectionFailed: "连接测试失败，请检查 API 配置。",
    aboutTitle: "内置工具",
    toolName: "工具",
    toolVersion: "固定版本",
    taskTitle: "任务和文件",
    taskHelp: "描述科研任务，并上传需要在本地处理的数据文件。",
    instructionPlaceholder: "示例：保留长度在 13 到 26 之间的肽序列，并导出 FASTA 文件。",
    uploadButton: "创建任务并上传",
    planTitle: "生成并验证 Workflow",
    planHelp: "模型生成 workflow，本地程序会先检查 skill 名称、输入和输出是否有效。",
    planButton: "生成 Workflow",
    workflowEmpty: "还没有生成 workflow。",
    runTitle: "本地执行",
    runHelp: "选择结果保存位置，审核 workflow，然后运行本地 skills。",
    selectOutputButton: "选择结果文件夹",
    outputEmpty: "还没有选择结果文件夹。",
    approvalText: "我已检查 workflow，并同意在本地运行这些 Skills。",
    executeButton: "运行 Workflow",
    runEmpty: "等待运行。",
    reportLink: "打开运行报告",
    working: "处理中...",
    uploading: "正在上传文件...",
    planning: "正在生成 workflow...",
    waitingFolder: "正在等待选择文件夹...",
    running: "正在本地运行 workflow...",
    openingPicker: "正在打开系统文件夹选择器...",
    workflowPlanningFailed: "Workflow 生成失败。",
    validationPassed: "验证通过。",
    validationReview: "验证需要检查。",
    localRunning: "本地执行正在运行。有些工具可能需要几分钟，请保持页面打开。",
  },
};
const t = (key) => translations[currentLanguage][key] || translations.en[key] || key;
const show = (id, value) => { $(id).textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2); };
const setConfigStatus = (key) => {
  configStatusKey = key;
  show("config-status", t(key));
};
const refreshPlanningControls = () => {
  $("plan").disabled = !(configurationReady && hasFiles);
};
const renderAboutTools = () => {
  const body = $("about-tools").querySelector("tbody");
  body.replaceChildren();
  for (const tool of aboutData?.tools || []) {
    const row = document.createElement("tr");
    const name = document.createElement("td");
    const version = document.createElement("td");
    name.textContent = tool.id;
    version.textContent = tool.version;
    row.append(name, version);
    body.append(row);
  }
};
const applyConfiguration = (config) => {
  $("api-base-url").value = config.base_url || "";
  $("api-model").value = config.model || "";
  $("api-key").value = "";
  apiKeyPresent = Boolean(config.api_key_present);
  configurationReady = false;
  refreshPlanningControls();
};
const safeResponseJson = async (response) => response.json().catch(() => ({}));
const clearReportLink = () => {
  if (reportObjectUrl) URL.revokeObjectURL(reportObjectUrl);
  reportObjectUrl = null;
  $("reportLink").hidden = true;
  $("reportLink").removeAttribute("href");
};
const loadReportLink = async () => {
  const response = await apiFetch(`/api/tasks/${taskId}/report`);
  if (!response.ok) throw new Error("report unavailable");
  if (reportObjectUrl) URL.revokeObjectURL(reportObjectUrl);
  reportObjectUrl = URL.createObjectURL(await response.blob());
  $("reportLink").href = reportObjectUrl;
  $("reportLink").hidden = false;
};
const setLanguage = (language) => {
  currentLanguage = translations[language] ? language : "en";
  document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  document.querySelectorAll(".lang-option").forEach((button) => {
    button.classList.toggle("active", button.dataset.language === currentLanguage);
  });
  ["save-api-config", "test-api-config", "upload", "plan", "selectOutput", "execute"].forEach((id) => {
    const button = $(id);
    button.dataset.defaultLabel = button.textContent;
  });
  if (configStatusKey) setConfigStatus(configStatusKey);
  renderAboutTools();
};
const setActivity = (message) => {
  $("activityBanner").hidden = !message;
  $("activityText").textContent = message || "";
};
const setButtonLoading = (buttonId, loading, label) => {
  const button = $(buttonId);
  if (!button.dataset.defaultLabel) button.dataset.defaultLabel = button.textContent;
  if (loading) button.dataset.wasDisabled = String(button.disabled);
  button.disabled = loading ? true : button.dataset.wasDisabled === "true";
  button.classList.toggle("loading", loading);
  button.textContent = loading ? label : button.dataset.defaultLabel;
  if (!loading) delete button.dataset.wasDisabled;
};
const setStepState = (step, state) => {
  document.querySelectorAll(".progress-step").forEach((item) => {
    if (item.dataset.step !== step) return;
    item.classList.remove("active", "done", "failed");
    item.classList.add(state);
  });
};
const resetAfterNewUpload = () => {
  workflow = null;
  workflowValid = false;
  outputDirectorySelected = false;
  hasFiles = false;
  $("approved").checked = false;
  show("workflowSummary", t("workflowEmpty"));
  show("workflow", t("workflowEmpty"));
  show("validation", "");
  show("runSummary", t("runEmpty"));
  show("status", t("runEmpty"));
  show("outputDirectory", t("outputEmpty"));
  clearReportLink();
  for (const step of ("plan output run").split(" ")) {
    const element = document.querySelector(`.progress-step[data-step="${step}"]`);
    element?.classList.remove("active", "done", "failed");
  }
  refreshPlanningControls();
};
const summarizeWorkflow = (data) => {
  const steps = data.workflow?.steps || [];
  const validText = data.validation?.valid ? t("validationPassed") : t("validationReview");
  return `Workflow generated. ${steps.length} step(s) planned. ${validText}`;
};
const summarizeRun = (data) => {
  const status = data.status || "unknown";
  const outputs = data.outputs?.length || 0;
  const exported = data.exported_files?.length || 0;
  return `Run ${status}. ${outputs} output(s), ${exported} exported file(s).`;
};
const refreshExecuteButton = () => {
  $("execute").disabled = !(workflowValid && outputDirectorySelected && $("approved").checked);
};

$("save-api-config").onclick = async () => {
  configurationReady = false;
  refreshPlanningControls();
  setButtonLoading("save-api-config", true, t("saveConfiguration"));
  try {
    const response = await apiFetch("/api/config", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        base_url: $("api-base-url").value,
        model: $("api-model").value,
        api_key: $("api-key").value.trim() || null
      })
    });
    const data = await safeResponseJson(response);
    if (!response.ok) {
      setConfigStatus("configurationUnavailable");
      return;
    }
    applyConfiguration(data);
    setConfigStatus("configurationSaved");
  } catch (_error) {
    setConfigStatus("configurationUnavailable");
  } finally {
    setButtonLoading("save-api-config", false);
  }
};

$("test-api-config").onclick = async () => {
  configurationReady = false;
  refreshPlanningControls();
  if (!apiKeyPresent) {
    setConfigStatus("configurationMissing");
    return;
  }
  setButtonLoading("test-api-config", true, t("testConnection"));
  try {
    const response = await apiFetch("/api/config/test", {method: "POST"});
    const data = await safeResponseJson(response);
    if (response.ok) {
      configurationReady = true;
      setConfigStatus("connectionPassed");
    } else if (data.detail?.error === "invalid_api_credentials") {
      setConfigStatus("invalidCredentials");
    } else if (data.detail?.error === "api_unreachable") {
      setConfigStatus("apiUnreachable");
    } else {
      setConfigStatus("connectionFailed");
    }
  } catch (_error) {
    setConfigStatus("apiUnreachable");
  } finally {
    setButtonLoading("test-api-config", false);
    refreshPlanningControls();
  }
};

$("upload").onclick = async () => {
  resetAfterNewUpload();
  setStepState("upload", "active");
  setActivity(t("uploading"));
  setButtonLoading("upload", true, t("uploading"));
  try {
    const created = await apiFetch("/api/tasks", {method: "POST"}).then(r => r.json());
    taskId = created.task_id;
    const body = new FormData();
    for (const file of $("files").files) body.append("files", file);
    const response = await apiFetch(`/api/tasks/${taskId}/files`, {method: "POST", body});
    const data = await response.json();
    show("fileList", data.files || data);
    hasFiles = Boolean(data.files?.length);
    refreshPlanningControls();
    $("selectOutput").disabled = !data.files?.length;
    setStepState("upload", response.ok && data.files?.length ? "done" : "failed");
    if (data.files?.length) setStepState("plan", "active");
  } catch (error) {
    show("fileList", `Upload failed: ${error.message}`);
    setStepState("upload", "failed");
  } finally {
    setButtonLoading("upload", false);
    setActivity("");
  }
};

$("plan").onclick = async () => {
  setStepState("plan", "active");
  setActivity(t("planning"));
  setButtonLoading("plan", true, t("planning"));
  try {
    const response = await apiFetch(`/api/tasks/${taskId}/plan`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({instruction: $("instruction").value})
    });
    const data = await response.json();
    if (!response.ok) {
      show("workflowSummary", t("workflowPlanningFailed"));
      show("workflow", data);
      setStepState("plan", "failed");
      return;
    }
    workflow = data.workflow;
    show("workflowSummary", summarizeWorkflow(data));
    show("workflow", workflow);
    show("validation", data.validation);
    workflowValid = data.validation.valid;
    setStepState("plan", workflowValid ? "done" : "failed");
    if (workflowValid) setStepState("output", "active");
  } catch (error) {
    show("workflowSummary", `Workflow planning failed: ${error.message}`);
    setStepState("plan", "failed");
  } finally {
    setButtonLoading("plan", false);
    setActivity("");
    refreshExecuteButton();
  }
};

$("selectOutput").onclick = async () => {
  setStepState("output", "active");
  setActivity(t("waitingFolder"));
  setButtonLoading("selectOutput", true, t("waitingFolder"));
  show("outputDirectory", t("openingPicker"));
  try {
    const response = await apiFetch(`/api/tasks/${taskId}/select-output-directory`, {method: "POST"});
    const data = await response.json();
    if (!response.ok) {
      outputDirectorySelected = false;
      const message = data.detail?.message || data.detail?.error || "No folder was selected.";
      show("outputDirectory", `Folder selection failed: ${message}`);
      setStepState("output", "failed");
    } else {
      outputDirectorySelected = true;
      show("outputDirectory", `Results will be saved to: ${data.path}`);
      setStepState("output", "done");
      setStepState("run", "active");
    }
  } catch (error) {
    outputDirectorySelected = false;
    show("outputDirectory", `Folder selection failed: ${error.message}`);
    setStepState("output", "failed");
  } finally {
    setButtonLoading("selectOutput", false);
    setActivity("");
  }
  refreshExecuteButton();
};

$("approved").onchange = refreshExecuteButton;

$("execute").onclick = async () => {
  setStepState("run", "active");
  setActivity(t("running"));
  setButtonLoading("execute", true, t("running"));
  show("runSummary", t("localRunning"));
  try {
    const response = await apiFetch(`/api/tasks/${taskId}/execute`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({approved: $("approved").checked, workflow})
    });
    const data = await response.json();
    show("status", data);
    show("runSummary", summarizeRun(data));
    if (response.ok) {
      try {
        await loadReportLink();
      } catch (_error) {
        clearReportLink();
      }
      setStepState("run", data.status === "failed" ? "failed" : "done");
    } else {
      clearReportLink();
      setStepState("run", "failed");
    }
  } catch (error) {
    show("runSummary", `Local execution failed: ${error.message}`);
    setStepState("run", "failed");
  } finally {
    setButtonLoading("execute", false);
    setActivity("");
    refreshExecuteButton();
  }
};

document.querySelectorAll(".lang-option").forEach((button) => {
  button.onclick = () => setLanguage(button.dataset.language);
});

const initializeDesktopInterface = async () => {
  setLanguage("en");
  try {
    const response = await apiFetch("/api/config");
    if (!response.ok) throw new Error("configuration unavailable");
    applyConfiguration(await safeResponseJson(response));
    setConfigStatus("configurationMissing");
  } catch (_error) {
    setConfigStatus("configurationUnavailable");
  }
  try {
    const response = await apiFetch("/api/about");
    if (!response.ok) return;
    const data = await safeResponseJson(response);
    aboutData = {tools: data.tools || []};
    renderAboutTools();
  } catch (_error) {
    renderAboutTools();
  }
};

initializeDesktopInterface();
