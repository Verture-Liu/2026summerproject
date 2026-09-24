let taskId = null;
let workflow = null;
let workflowValid = false;
let outputDirectorySelected = false;
let currentLanguage = "en";
let configurationReady = false;
let apiKeyPresent = false;
const savedConfiguration = {baseUrl: "", model: ""};
let missingConfigurationFieldKeys = [];
let configurationGeneration = 0;
let hasFiles = false;
let configStatusKey = "";
let aboutData = null;
let sessionToken = "";
let sessionInvalid = false;
let reportObjectUrl = null;
let lastValidation = null;

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
const apiFetch = async (path, options = {}) => {
  const response = await fetch(path, {
    ...options,
    headers: {...options.headers, "X-PaleoRigor-Token": sessionToken}
  });
  if (response.status === 401) {
    const error = await response.clone().json().catch(() => ({}));
    if (error.detail?.error === "invalid_session") markSessionInvalid();
  }
  return response;
};
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
    deleteApiKey: "Delete API Key",
    configurationSaved: "Configuration saved.",
    configurationFieldsMissing: "Missing required configuration: {fields}.",
    apiKeyDeleted: "API key deleted.",
    apiKeyDeleteFailed: "The API key could not be deleted. Try again.",
    connectionPassed: "Connection passed.",
    invalidCredentials: "Invalid API credentials.",
    apiUnreachable: "The API could not be reached.",
    configurationMissing: "Complete and test the API configuration before planning a workflow.",
    configurationUnavailable: "Configuration is unavailable. Try again.",
    connectionFailed: "The connection test failed. Check the API configuration.",
    invalidSession: "This browser session is no longer valid. Quit and relaunch PaleoRigor to continue.",
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
    tagAgent: "Agent",
    tagConstraint: "Constraint",
    tagReproducibility: "Reproducibility",
    coreCaption: "stages complete",
    fileRecords: "records",
    runLogEmpty: "No run recorded yet.",
    flowTitle: "Planned",
    flowTitleAccent: "dataflow",
    flowLegend: "Hover a node to see what it does. Every edge is an input the validator resolved before the run was allowed.",
    flowMetaTemplate: "{skills} skills · {edges} edges · {unresolved} unresolved",
    flowInputs: "uploaded",
    flowSkills: "skills",
    flowRetained: "retained",
    flowUploaded: "uploaded file",
    metricSteps: "Steps",
    metricInputs: "Inputs resolved",
    metricUnknown: "Unknown skills",
    metricWarnings: "Warnings",
    validationOk: "Validation passed. Every input resolved, no unknown skills.",
    issueHint: "Suggested fix",
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
    deleteApiKey: "删除 API 密钥",
    configurationSaved: "配置已保存。",
    configurationFieldsMissing: "缺少必填配置：{fields}。",
    apiKeyDeleted: "API 密钥已删除。",
    apiKeyDeleteFailed: "无法删除 API 密钥，请重试。",
    connectionPassed: "连接测试通过。",
    invalidCredentials: "API 凭据无效。",
    apiUnreachable: "无法连接 API。",
    configurationMissing: "请先完成并测试 API 配置，再生成 workflow。",
    configurationUnavailable: "配置暂时不可用，请重试。",
    connectionFailed: "连接测试失败，请检查 API 配置。",
    invalidSession: "此浏览器会话已失效。请退出并重新启动 PaleoRigor 后继续。",
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
    tagAgent: "智能体",
    tagConstraint: "约束",
    tagReproducibility: "可重复性",
    coreCaption: "个阶段已完成",
    fileRecords: "条记录",
    runLogEmpty: "尚无运行记录。",
    flowTitle: "已规划的",
    flowTitleAccent: "数据流",
    flowLegend: "悬停节点查看它做什么。每条边都是校验层在放行前已解析的输入。",
    flowMetaTemplate: "{skills} 个技能 · {edges} 条边 · {unresolved} 项未解析",
    flowInputs: "上传文件",
    flowSkills: "技能",
    flowRetained: "保留产物",
    flowUploaded: "上传文件",
    metricSteps: "步骤",
    metricInputs: "输入已解析",
    metricUnknown: "未知技能",
    metricWarnings: "警告",
    validationOk: "校验通过。输入全部解析，无未知技能。",
    issueHint: "修复建议",
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
  if (sessionInvalid && key !== "invalidSession") return;
  missingConfigurationFieldKeys = [];
  configStatusKey = key;
  show("config-status", t(key));
};
const setMissingConfigurationStatus = (fieldKeys) => {
  missingConfigurationFieldKeys = [...fieldKeys];
  configStatusKey = "";
  const fields = fieldKeys.map((key) => t(key)).join(", ");
  show("config-status", t("configurationFieldsMissing").replace("{fields}", fields));
};
const missingConfigurationFields = (useSavedValues = false) => {
  const baseUrl = useSavedValues ? savedConfiguration.baseUrl : $("api-base-url").value.trim();
  const model = useSavedValues ? savedConfiguration.model : $("api-model").value.trim();
  const missing = [];
  if (!baseUrl) missing.push("baseUrl");
  if (!model) missing.push("model");
  if (!(apiKeyPresent || (!useSavedValues && $("api-key").value.trim()))) missing.push("apiKey");
  return missing;
};
const isCurrentConfigurationAction = (generation) => generation === configurationGeneration;
const configurationActionButtonIds = [
  "save-api-config",
  "test-api-config",
  "delete-api-key",
];
const configurationMutationControlIds = [
  "api-base-url",
  "api-model",
  "api-key",
  "save-api-config",
  "test-api-config",
  "delete-api-key",
];
const setConfigurationMutationPending = (pending) => {
  configurationMutationControlIds.forEach((controlId) => {
    $(controlId).disabled = pending || sessionInvalid;
  });
};
const resetConfigurationActionButtons = () => {
  configurationActionButtonIds.forEach((buttonId) => setButtonLoading(buttonId, false));
};
const beginConfigurationAction = (buttonId, label, mutatesConfiguration = false) => {
  const generation = ++configurationGeneration;
  resetConfigurationActionButtons();
  if (mutatesConfiguration) setConfigurationMutationPending(true);
  setButtonLoading(buttonId, true, label);
  return generation;
};
const completeConfigurationAction = (generation, mutatesConfiguration = false) => {
  if (!isCurrentConfigurationAction(generation)) return;
  resetConfigurationActionButtons();
  if (mutatesConfiguration) setConfigurationMutationPending(false);
};
const refreshPlanningControls = () => {
  $("plan").disabled = sessionInvalid || !(configurationReady && hasFiles);
  setStepState("api", configurationReady ? "done" : "active");
};
const markSessionInvalid = () => {
  if (sessionInvalid) return;
  sessionInvalid = true;
  configurationReady = false;
  setConfigStatus("invalidSession");
  setConfigurationMutationPending(true);
  ["upload", "plan", "selectOutput", "execute", "approved", "files"].forEach((controlId) => {
    $(controlId).disabled = true;
  });
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
  savedConfiguration.baseUrl = config.base_url || "";
  savedConfiguration.model = config.model || "";
  $("api-base-url").value = savedConfiguration.baseUrl;
  $("api-model").value = savedConfiguration.model;
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
  ["save-api-config", "test-api-config", "delete-api-key", "upload", "plan", "selectOutput", "execute"].forEach((id) => {
    const button = $(id);
    button.dataset.defaultLabel = button.textContent;
  });
  if (workflow) renderDataflow(workflow, lastValidation);
  if (lastValidation) renderValidationIssues(lastValidation);
  if (missingConfigurationFieldKeys.length) {
    setMissingConfigurationStatus(missingConfigurationFieldKeys);
  } else if (configStatusKey) {
    setConfigStatus(configStatusKey);
  }
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
  button.disabled = sessionInvalid || (loading ? true : button.dataset.wasDisabled === "true");
  button.setAttribute("aria-busy", String(loading));
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
const SVG_NS = "http://www.w3.org/2000/svg";
const svgNode = (name, attributes = {}) => {
  const node = document.createElementNS(SVG_NS, name);
  for (const key of Object.keys(attributes)) node.setAttribute(key, attributes[key]);
  return node;
};
const svgLabel = (className, x, y, text) => {
  const node = svgNode("text", {class: className, x, y});
  node.textContent = text;
  return node;
};
const normalizeStepReference = (reference) => String(reference || "").split(".")[0];
const shortenLabel = (text, width) => {
  const limit = Math.max(6, Math.floor((width - 34) / 6.5));
  const value = String(text || "");
  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
};

// Lay the planned workflow out left to right: the uploaded files, then one lane
// per dependency depth, then the outputs that no later step consumes.
const buildDataflowModel = (plan) => {
  const steps = (plan?.steps || []).filter((step) => step && step.skill);
  const stepsById = new Map(steps.map((step) => [step.id, step]));

  // A step input may name an earlier output as "step_03.fastqc_zip", as the
  // bare alias "fastqc_zip", or as the whole step directory "step_03" — the
  // validator accepts all three, so the picture has to resolve all three.
  const outputOwner = new Map();
  for (const step of steps) {
    for (const output of step.outputs || []) {
      outputOwner.set(`${step.id}.${output.name}`, step.id);
      if (!outputOwner.has(output.name)) outputOwner.set(output.name, step.id);
    }
  }
  const producerOf = (reference) => {
    const raw = String(reference || "");
    const head = normalizeStepReference(raw);
    if (raw.includes(".") && stepsById.has(head)) return stepsById.get(head);
    const owner = outputOwner.get(raw);
    if (owner) return stepsById.get(owner);
    return stepsById.get(head);
  };
  const outputNameOf = (reference) => {
    const raw = String(reference || "");
    return raw.includes(".") ? raw.slice(raw.indexOf(".") + 1) : raw;
  };

  const depths = new Map();
  const depthOf = (step, seen) => {
    if (depths.has(step.id)) return depths.get(step.id);
    if (seen.has(step.id)) return 0;
    seen.add(step.id);
    let depth = 0;
    for (const input of step.inputs || []) {
      if (input?.source !== "step") continue;
      const producer = producerOf(input.ref);
      if (producer && producer.id !== step.id) depth = Math.max(depth, depthOf(producer, seen) + 1);
    }
    depths.set(step.id, depth);
    return depth;
  };
  steps.forEach((step) => depthOf(step, new Set()));

  const uploads = [];
  const consumedOutputs = new Set();
  const consumedSteps = new Set();
  let inputCount = 0;
  let unresolved = 0;
  for (const step of steps) {
    for (const input of step.inputs || []) {
      inputCount += 1;
      if (input?.source === "step") {
        const producer = producerOf(input.ref);
        if (!producer) {
          unresolved += 1;
        } else if (String(input.ref) === producer.id) {
          consumedSteps.add(producer.id);
        } else {
          consumedOutputs.add(`${producer.id}.${outputNameOf(input.ref)}`);
        }
      } else if (input?.ref && !uploads.includes(input.ref)) {
        uploads.push(input.ref);
      }
    }
  }
  const retained = [];
  for (const step of steps) {
    if (consumedSteps.has(step.id)) continue;
    for (const output of step.outputs || []) {
      if (consumedOutputs.has(`${step.id}.${output.name}`)) continue;
      retained.push({step, name: output.name, format: output.format});
    }
  }
  const maxDepth = steps.length ? Math.max(...steps.map((step) => depths.get(step.id) || 0)) : 0;
  return {steps, depths, uploads, retained, maxDepth, inputCount, unresolved, stepsById, producerOf};
};

const clearDataflow = () => {
  $("flowStage").classList.add("is-hidden");
  $("flowStage").classList.remove("is-running");
  ["flowAxis", "flowEdges", "flowParts", "flowNodes"].forEach((id) => $(id).replaceChildren());
  $("workflow").hidden = false;
};

const renderDataflow = (plan, validation) => {
  const model = buildDataflowModel(plan);
  if (!model.steps.length) {
    clearDataflow();
    return;
  }
  const lanes = [];
  lanes.push(model.uploads.map((ref) => ({
    kind: "chip", key: `up:${ref}`, title: ref, subtitle: t("flowUploaded")
  })));
  for (let level = 0; level <= model.maxDepth; level += 1) {
    lanes.push(
      model.steps
        .filter((step) => (model.depths.get(step.id) || 0) === level)
        .map((step) => ({
          kind: "skill", key: step.id, step,
          title: step.skill, subtitle: step.id, reason: step.reason
        }))
    );
  }
  lanes.push(model.retained.map((item) => ({
    kind: "chip", keep: true, key: `out:${item.step.id}.${item.name}`,
    title: item.name, subtitle: item.format
  })));

  const used = lanes.filter((lane) => lane.length);
  const laneCount = used.length || 1;
  const width = 1120;
  const nodeWidth = Math.max(112, Math.min(212, Math.floor((width - (laneCount - 1) * 54) / laneCount)));
  const gap = laneCount > 1 ? (width - laneCount * nodeWidth) / (laneCount - 1) : 0;
  const rows = Math.max(1, ...used.map((lane) => lane.length));
  const height = Math.max(250, rows * 78);

  const placed = new Map();
  used.forEach((lane, laneIndex) => {
    const x = Math.round(laneIndex * (nodeWidth + gap));
    lane.forEach((node, rowIndex) => {
      const centre = 22 + ((height - 44) * (rowIndex + 0.5)) / lane.length;
      placed.set(node.key, {
        ...node, x, y: Math.round(centre), w: nodeWidth, h: node.kind === "skill" ? 52 : 44
      });
    });
  });

  const edges = [];
  const link = (fromKey, toKey) => {
    const from = placed.get(fromKey);
    const to = placed.get(toKey);
    if (from && to) edges.push({from, to});
  };
  for (const step of model.steps) {
    for (const input of step.inputs || []) {
      if (input?.source === "step") {
        const producer = model.producerOf(input.ref);
        if (producer) link(producer.id, step.id);
      } else if (input?.ref) {
        link(`up:${input.ref}`, step.id);
      }
    }
  }
  for (const item of model.retained) link(item.step.id, `out:${item.step.id}.${item.name}`);

  const axis = $("flowAxis");
  const edgeLayer = $("flowEdges");
  const partLayer = $("flowParts");
  const nodeLayer = $("flowNodes");
  [axis, edgeLayer, partLayer, nodeLayer].forEach((layer) => layer.replaceChildren());

  $("flowSvg").setAttribute("viewBox", `0 0 ${width} ${height + 32}`);
  axis.append(svgNode("line", {class: "ax", x1: 0, y1: height + 6, x2: width, y2: height + 6}));
  used.forEach((lane, laneIndex) => {
    let name = t("flowSkills");
    if (laneIndex === 0 && model.uploads.length) name = t("flowInputs");
    else if (laneIndex === used.length - 1 && model.retained.length) name = t("flowRetained");
    else if (laneIndex !== 1) return;
    axis.append(svgLabel("ax-t", Math.round(laneIndex * (nodeWidth + gap)), height + 24, name));
  });

  edges.forEach((edge, index) => {
    const x1 = edge.from.x + edge.from.w;
    const y1 = edge.from.y;
    const x2 = edge.to.x;
    const y2 = edge.to.y;
    const bend = Math.max(26, (x2 - x1) / 2);
    edgeLayer.append(svgNode("path", {
      class: "e", id: `flow-e${index}`,
      d: `M${x1} ${y1} C${x1 + bend} ${y1} ${x2 - bend} ${y2} ${x2} ${y2}`
    }));
    if (index < 14) {
      const dot = svgNode("circle", {class: "pt", r: 2.4});
      const motion = svgNode("animateMotion", {
        dur: `${(2.4 + (index % 5) * 0.28).toFixed(2)}s`,
        begin: `${((index % 4) * 0.35).toFixed(2)}s`,
        repeatCount: "indefinite"
      });
      const mpath = svgNode("mpath", {href: `#flow-e${index}`});
      mpath.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", `#flow-e${index}`);
      motion.append(mpath);
      dot.append(motion);
      partLayer.append(dot);
    }
  });

  for (const node of placed.values()) {
    const group = svgNode("g", {class: "gnode"});
    const tip = svgNode("title");
    tip.textContent = node.reason ? `${node.title} — ${node.reason}` : node.title;
    group.append(tip);
    group.append(svgNode("rect", {
      class: node.kind === "skill" ? "n-sk" : "n-chip",
      x: node.x, y: Math.round(node.y - node.h / 2),
      width: node.w, height: node.h,
      rx: node.kind === "skill" ? 10 : 9
    }));
    if (node.kind === "chip") {
      group.append(svgNode("path", {
        class: node.keep ? "gl gl-k" : "gl",
        transform: `translate(${node.x + 12},${node.y - 7}) scale(.58)`,
        d: "M14 3v5h5M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7z"
      }));
      group.append(svgLabel("t-1", node.x + 30, node.y - 1, shortenLabel(node.title, node.w)));
      group.append(svgLabel("t-2", node.x + 30, node.y + 12, shortenLabel(node.subtitle, node.w)));
    } else {
      group.append(svgLabel("t-1", node.x + 16, node.y - 1, shortenLabel(node.title, node.w + 14)));
      group.append(svgLabel("t-2", node.x + 16, node.y + 13, shortenLabel(node.subtitle, node.w + 14)));
    }
    nodeLayer.append(group);
  }

  const issues = validation?.issues || [];
  const unknownSkills = issues.filter((issue) => issue?.code === "unknown_skill").length;
  $("metricSteps").textContent = String(model.steps.length);
  $("metricInputs").textContent = `${model.inputCount - model.unresolved}/${model.inputCount}`;
  $("metricUnknown").textContent = String(unknownSkills);
  $("metricWarnings").textContent = String((validation?.warnings || []).length);
  $("flowMeta").textContent = t("flowMetaTemplate")
    .replace("{skills}", String(model.steps.length))
    .replace("{edges}", String(edges.length))
    .replace("{unresolved}", String(model.unresolved));

  $("flowStage").classList.remove("is-hidden");
  $("workflow").hidden = true;
};

// The validator already explains itself; show that rather than a JSON dump.
const renderValidationIssues = (validation) => {
  const host = $("validation");
  host.replaceChildren();
  if (!validation) return;
  const issues = validation.issues || [];
  const errors = validation.errors || [];
  if (validation.valid && !issues.length) {
    const passed = document.createElement("p");
    passed.className = "validation-ok";
    passed.textContent = t("validationOk");
    host.append(passed);
    return;
  }
  const list = document.createElement("ul");
  list.className = "issues";
  const entries = issues.length ? issues : errors.map((message) => ({code: "error", message}));
  for (const issue of entries) {
    const item = document.createElement("li");
    item.className = validation.valid ? "issue warn" : "issue";
    const code = document.createElement("span");
    code.className = "code";
    code.textContent = issue.code || "issue";
    const body = document.createElement("div");
    const message = document.createElement("p");
    message.className = "msg";
    message.textContent = issue.message || "";
    body.append(message);
    if (issue.step_id || issue.skill) {
      const where = document.createElement("p");
      where.className = "where";
      where.textContent = [issue.step_id || "", issue.skill || ""].filter(Boolean).join(" · ");
      body.append(where);
    }
    if (issue.hint) {
      const hint = document.createElement("p");
      hint.className = "hint";
      hint.textContent = `${t("issueHint")}: ${issue.hint}`;
      body.append(hint);
    }
    item.append(code, body);
    list.append(item);
  }
  host.append(list);
};
const formatBytes = (bytes) => {
  const value = Number(bytes);
  if (!Number.isFinite(value) || value < 0) return "";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value, unit = 0;
  while (size >= 1024 && unit < units.length - 1) { size /= 1024; unit += 1; }
  return `${size >= 10 || unit === 0 ? Math.round(size) : size.toFixed(1)} ${units[unit]}`;
};
const renderFileList = (files) => {
  const host = $("fileList");
  if (!Array.isArray(files) || !files.length) {
    show("fileList", files);
    return;
  }
  host.replaceChildren();
  const list = document.createElement("ul");
  list.className = "files";
  for (const file of files) {
    const summary = file?.summary || {};
    const item = document.createElement("li");
    item.className = "file";
    const glyph = document.createElement("span");
    glyph.className = "file-glyph";
    glyph.setAttribute("aria-hidden", "true");
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("class", "ic");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", "#i-doc");
    icon.append(use);
    glyph.append(icon);
    const name = document.createElement("span");
    name.className = "file-name";
    name.textContent = summary.name || file?.ref || "";
    name.title = name.textContent;
    const meta = document.createElement("span");
    meta.className = "file-meta";
    const format = document.createElement("b");
    format.textContent = String(summary.format || "file").toUpperCase();
    const details = [formatBytes(summary.size_bytes)];
    if (Number.isFinite(summary.record_count)) details.push(`${summary.record_count} ${t("fileRecords")}`);
    if (file?.sha256) details.push(`sha256 ${String(file.sha256).slice(0, 12)}`);
    meta.append(format, document.createTextNode(` · ${details.filter(Boolean).join(" · ")}`));
    item.append(glyph, name, meta);
    list.append(item);
  }
  host.append(list);
};
const resetAfterNewUpload = () => {
  workflow = null;
  workflowValid = false;
  lastValidation = null;
  clearDataflow();
  outputDirectorySelected = false;
  hasFiles = false;
  $("approved").checked = false;
  show("workflowSummary", t("workflowEmpty"));
  show("workflow", t("workflowEmpty"));
  show("validation", "");
  show("runSummary", t("runEmpty"));
  show("status", t("runLogEmpty"));
  show("outputDirectory", t("outputEmpty"));
  clearReportLink();
  for (const step of ("plan output run").split(" ")) {
    const element = document.querySelector(`.progress-step[data-step="${step}"]`);
    element?.classList.remove("active", "done", "failed");
  }
  refreshPlanningControls();
  $("workflow").hidden = true;
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
  $("execute").disabled = sessionInvalid || !(workflowValid && outputDirectorySelected && $("approved").checked);
};

$("save-api-config").onclick = async () => {
  const missingFields = missingConfigurationFields();
  if (missingFields.length) {
    setMissingConfigurationStatus(missingFields);
    return;
  }
  const requestGeneration = beginConfigurationAction("save-api-config", t("saveConfiguration"), true);
  configurationReady = false;
  refreshPlanningControls();
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
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    const data = await safeResponseJson(response);
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    if (!response.ok) {
      setConfigStatus("configurationUnavailable");
      return;
    }
    applyConfiguration(data);
    setConfigStatus("configurationSaved");
  } catch (_error) {
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    setConfigStatus("configurationUnavailable");
  } finally {
    completeConfigurationAction(requestGeneration, true);
  }
};

$("test-api-config").onclick = async () => {
  const missingFields = missingConfigurationFields(true);
  if (missingFields.length) {
    setMissingConfigurationStatus(missingFields);
    return;
  }
  const requestGeneration = beginConfigurationAction("test-api-config", t("testConnection"));
  configurationReady = false;
  refreshPlanningControls();
  try {
    const response = await apiFetch("/api/config/test", {method: "POST"});
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    const data = await safeResponseJson(response);
    if (!isCurrentConfigurationAction(requestGeneration)) return;
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
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    setConfigStatus("apiUnreachable");
  } finally {
    completeConfigurationAction(requestGeneration);
    refreshPlanningControls();
  }
};

$("delete-api-key").onclick = async () => {
  const requestGeneration = beginConfigurationAction("delete-api-key", t("deleteApiKey"), true);
  configurationReady = false;
  $("api-key").value = "";
  refreshPlanningControls();
  try {
    const response = await apiFetch("/api/config/key", {method: "DELETE"});
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    const data = await safeResponseJson(response);
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    if (!response.ok) {
      setConfigStatus("apiKeyDeleteFailed");
      return;
    }
    applyConfiguration(data);
    apiKeyPresent = false;
    configurationReady = false;
    refreshPlanningControls();
    setConfigStatus("apiKeyDeleted");
  } catch (_error) {
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    setConfigStatus("apiKeyDeleteFailed");
  } finally {
    completeConfigurationAction(requestGeneration, true);
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
    renderFileList(data.files || data);
    hasFiles = Boolean(data.files?.length);
    refreshPlanningControls();
    $("selectOutput").disabled = sessionInvalid || !data.files?.length;
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
      lastValidation = null;
      clearDataflow();
      setStepState("plan", "failed");
      return;
    }
    workflow = data.workflow;
    lastValidation = data.validation;
    show("workflowSummary", summarizeWorkflow(data));
    show("workflow", workflow);
    renderDataflow(workflow, data.validation);
    renderValidationIssues(data.validation);
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

const loadInitialConfiguration = async () => {
  const requestGeneration = configurationGeneration;
  try {
    const response = await apiFetch("/api/config");
    if (!response.ok) throw new Error("configuration unavailable");
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    const data = await safeResponseJson(response);
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    applyConfiguration(data);
    const missingFields = missingConfigurationFields(true);
    if (missingFields.length) {
      setMissingConfigurationStatus(missingFields);
    } else {
      setConfigStatus("configurationMissing");
    }
  } catch (_error) {
    if (!isCurrentConfigurationAction(requestGeneration)) return;
    setConfigStatus("configurationUnavailable");
  }
};

const initializeDesktopInterface = async () => {
  setLanguage("en");
  await loadInitialConfiguration();
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
