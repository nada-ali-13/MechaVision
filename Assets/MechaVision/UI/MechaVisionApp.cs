using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using MechaVision.AR;
using MechaVision.Catalog;
using MechaVision.Rendering;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.Scripting;
using UnityEngine.UI;

namespace MechaVision.UI
{
    public sealed class MechaVisionApp : MonoBehaviour
    {
        public BoardTracker tracker;
        public BoardAssembly assembly;

        private enum Page { Tracking, Catalog, Project, Sketch, Calibration }

        private static readonly string[] Levels = { "", "beginner", "intermediate", "advanced" };
        private const string JavaDocuments = "com.mechavision.documents.SketchDocuments";

        private CatalogData catalog;
        private ProjectData selected;
        private ProjectData assembling;
        private int step;
        private bool previewMode;
        private bool showDrafts;
        private bool overlayVisible = true;
        private bool saving;
        private string pendingProject;
        private string savedProject;
        private string sketch;
        private string documentPath;
        private string sketchStatus;
        private Page page;
        private string query = "";
        private string category = "";
        private int levelIndex;
        private AppView view;
        private AssemblyPreview preview;
        private RectTransform overlay;
        private RectTransform body;
        private RectTransform results;
        private ArabicLabel searchCaption;
        private ArabicLabel levelCaption;
        private ArabicLabel trackingStatus;
        private ArabicLabel stepTitle;
        private ArabicLabel stepInstruction;
        private ArabicLabel sketchStatusLabel;
        private Button previousButton;
        private Button nextButton;
        private Button saveButton;
        private Button openButton;
        private Button shareButton;
        private Rect lastSafeArea;
        private Vector2Int lastScreenSize;
        private Vector3 initialOffset;
        private Vector3 initialRotation;
        private TouchScreenKeyboard searchKeyboard;

        private void Start()
        {
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            if (tracker != null)
            {
                initialOffset = tracker.Calibration.OffsetMillimetres;
                initialRotation = tracker.Calibration.RotationDegrees;
            }

            try
            {
                catalog = CatalogLoader.Load();
            }
            catch (Exception error)
            {
                // The standalone alignment demo remains usable without the catalog.
                Debug.LogException(error, this);
            }

            Font arabicFont = Resources.Load<Font>("MechaVision/Fonts/DejaVuSans");
            Font codeFont = Resources.Load<Font>("MechaVision/Fonts/DejaVuSansMono");
            view = new AppView(arabicFont, codeFont);
            if (tracker != null && assembly != null)
                assembly.Configure(tracker.BoardRoot, catalog);
            previewMode = Application.platform != RuntimePlatform.Android || tracker == null || assembly == null;
            BuildCanvas();
            Show(Page.Tracking);
        }

        private void Update()
        {
            UpdateSafeArea();
            if (page == Page.Tracking && trackingStatus != null && !previewMode && tracker != null)
            {
                trackingStatus.color = tracker.IsTracking ? AppView.Mint : AppView.Amber;
                trackingStatus.SetContent(tracker.StatusArabic);
            }

            if (searchKeyboard != null)
            {
                if (searchKeyboard.status != TouchScreenKeyboard.Status.Canceled)
                    SetQuery(searchKeyboard.text);
                if (searchKeyboard.status != TouchScreenKeyboard.Status.Visible)
                    searchKeyboard = null;
            }
        }

        private void OnDestroy()
        {
            preview?.Dispose();
            view?.Dispose();
        }

        private void BuildCanvas()
        {
            var canvasObject = new GameObject("MechaVision interface", typeof(RectTransform));
            canvasObject.transform.SetParent(transform, false);
            var canvas = canvasObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 5;
            var scaler = canvasObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(560, 960);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.Expand;
            canvasObject.AddComponent<GraphicRaycaster>();

            if (FindAnyObjectByType<EventSystem>() == null)
            {
                var input = new GameObject("User input", typeof(EventSystem));
                input.transform.SetParent(transform, false);
                input.AddComponent<InputSystemUIInputModule>();
            }

            overlay = AppView.Rect(canvas.transform, "Safe area");
            UpdateSafeArea();
        }

        private void UpdateSafeArea()
        {
            if (overlay == null || Screen.width < 1 || Screen.height < 1)
                return;

            Rect safeArea = Screen.safeArea;
            var screenSize = new Vector2Int(Screen.width, Screen.height);
            if (safeArea == lastSafeArea && screenSize == lastScreenSize)
                return;
            lastSafeArea = safeArea;
            lastScreenSize = screenSize;
            var size = new Vector2(screenSize.x, screenSize.y);
            overlay.anchorMin = safeArea.min / size;
            overlay.anchorMax = safeArea.max / size;
            overlay.offsetMin = Vector2.zero;
            overlay.offsetMax = Vector2.zero;
        }

        private void Show(Page next)
        {
            page = next;
            assembly?.Clear();
            preview?.Hide();
            AppView.Clear(overlay);
            RectTransform content = view.Stack(overlay, "Screen", 10f, 12);
            AppView.Fill(content);
            if (page != Page.Tracking || previewMode)
                view.Plate(content, AppView.Background);
            BuildHeader(content);
            body = view.Stack(content, "Page", 9f);
            AppView.Height(body, 0, 1);

            switch (page)
            {
                case Page.Tracking: BuildTracking(); break;
                case Page.Catalog: BuildCatalog(); break;
                case Page.Project: BuildProject(); break;
                case Page.Sketch: BuildSketch(); break;
                case Page.Calibration: BuildCalibration(); break;
            }
        }

        private void BuildHeader(RectTransform parent)
        {
            RectTransform header = view.Card(parent, "Header");
            RectTransform heading = view.Row(header, "Brand");
            ArabicLabel name = view.Label(heading, "MechaVision", 26, AppView.Mint);
            AppView.Height(name.rectTransform, 38);
            RectTransform tabs = view.Row(header, "Navigation");
            view.Button(tabs, "الواقع المعزز", () => Show(Page.Tracking),
                page == Page.Tracking || page == Page.Calibration, 19, 44);
            view.Button(tabs, "المشاريع", () => Show(Page.Catalog),
                page != Page.Tracking && page != Page.Calibration, 19, 44);
        }

        private void BuildCatalog()
        {
            if (catalog == null)
            {
                view.Label(body, "تعذر تحميل مكتبة المشاريع المحلية.", 22, AppView.Amber);
                return;
            }

            if (TouchScreenKeyboard.isSupported)
            {
                Button button = view.Button(body, QueryCaption(),
                    () => searchKeyboard = TouchScreenKeyboard.Open(query, TouchScreenKeyboardType.Default,
                        false, false, false, false, "ابحث بالعربية أو الإنجليزية"));
                searchCaption = button.GetComponentInChildren<ArabicLabel>();
            }
            else
            {
                view.Input(body, query, "ابحث بالعربية أو الإنجليزية", false).onValueChanged.AddListener(SetQuery);
            }

            string[] categories = catalog.projects.Select(project => project.category).Distinct().OrderBy(value => value).ToArray();
            RectTransform filters = view.Row(body, "Filters");
            Button categoryButton = null;
            categoryButton = view.Button(filters, "الفئة • " + CategoryName(category), () =>
            {
                int next = Array.IndexOf(categories, category) + 1;
                category = next >= categories.Length ? "" : categories[next];
                categoryButton.GetComponentInChildren<ArabicLabel>().SetContent("الفئة • " + CategoryName(category));
                PopulateResults();
            }, size: 17, height: 48);
            Button levelButton = view.Button(filters, "المستوى • " + LevelName(Levels[levelIndex]), () =>
            {
                levelIndex = (levelIndex + 1) % Levels.Length;
                levelCaption.SetContent("المستوى • " + LevelName(Levels[levelIndex]));
                PopulateResults();
            }, size: 17, height: 48);
            levelCaption = levelButton.GetComponentInChildren<ArabicLabel>();
            Button draftsButton = null;
            draftsButton = view.Button(body, DraftToggleCaption(), () =>
            {
                showDrafts = !showDrafts;
                draftsButton.GetComponentInChildren<ArabicLabel>().SetContent(DraftToggleCaption());
                PopulateResults();
            }, size: 19, height: 48);

            results = view.Scroll(body, "Projects");
            PopulateResults();
        }

        private void SetQuery(string value)
        {
            if (query == value)
                return;
            query = value;
            if (page != Page.Catalog)
                return;
            if (searchCaption != null)
                searchCaption.SetContent(QueryCaption());
            PopulateResults();
        }

        private string DraftToggleCaption() => showDrafts ? "عرض المشاريع المتحقق منها فقط" : "عرض المسودات التعليمية";

        private string QueryCaption() => string.IsNullOrEmpty(query) ? "ابحث بالعربية أو الإنجليزية" : "البحث • " + query;

        private void PopulateResults()
        {
            AppView.Clear(results);
            ProjectData[] matches = catalog.projects
                .Where(project => (showDrafts || project.verification?.status == "verified") &&
                    CatalogNavigation.Matches(project, query, category, Levels[levelIndex]))
                .ToArray();
            string summary = $"المشاريع • {matches.Length}";
            if (matches.Length == 0)
            {
                summary = showDrafts ? "لا توجد مشاريع تطابق البحث." :
                    "لا توجد مشاريع متحقق منها تطابق البحث. يمكنك عرض المسودات التعليمية.";
            }
            view.Label(results, summary, 18, AppView.Secondary);
            foreach (ProjectData project in matches)
            {
                RectTransform card = view.Card(results, project.id);
                view.Button(card, project.name_ar, () => Select(project), size: 22);
                view.Label(card, project.name_en, 17, AppView.Secondary);
                view.Label(card, $"{CategoryName(project.category)} • {LevelName(project.level)} • {ReviewName(project)}", 17, AppView.Amber);
            }

            if (results.parent.parent.TryGetComponent(out ScrollRect scroll))
                scroll.verticalNormalizedPosition = 1;
        }

        private void Select(ProjectData project)
        {
            selected = project;
            Show(Page.Project);
        }

        private void BuildProject()
        {
            RectTransform details = view.Scroll(body, "Project details");
            RectTransform intro = view.Card(details, "Project");
            view.Label(intro, selected.name_ar, 27);
            view.Label(intro, selected.name_en, 19, AppView.Secondary);
            view.Label(intro, selected.description_ar);
            view.Label(intro, ReviewName(selected), 18, AppView.Amber);
            if (selected.verification?.status != "verified")
                view.Label(intro, "راجع التوصيلات ومصدر الطاقة مع المعلّم قبل تشغيل الدائرة.", 18, AppView.Amber);

            RectTransform components = view.Card(details, "Components");
            view.Label(components, "المكونات", 24, AppView.Mint);
            foreach (var group in selected.components.GroupBy(component => component.part_id))
            {
                PartData part = Array.Find(catalog.parts, item => item.id == group.Key);
                int quantity = group.Sum(component => component.qty);
                view.Label(components, $"{part?.name_ar ?? group.Key} × {quantity}", 20);
            }

            RectTransform power = view.Card(details, "Power");
            view.Label(power, "التغذية الكهربائية", 24, AppView.Mint);
            view.Label(power, selected.electrical_constraints.supply_notes_ar, 19);
            foreach (string warning in selected.electrical_constraints.warnings_ar)
                view.Label(power, warning, 19, AppView.Amber);

            RectTransform connections = view.Card(details, "Connections");
            view.Label(connections, "التوصيلات والخطوات", 24, AppView.Mint);
            foreach (AssemblyStepData item in selected.assembly_steps)
            {
                view.Label(connections, $"{item.step}. {item.instruction_ar}", 19);
                string terminals = StepTerminals(selected, item);
                if (terminals.Length > 0)
                    view.Label(connections, terminals, 17, AppView.Secondary);
            }

            RectTransform sources = view.Card(details, "Sources");
            view.Label(sources, "المصادر", 24, AppView.Mint);
            foreach (SourceData source in selected.sources)
            {
                view.Label(sources, source.purpose, 18);
                if (Uri.TryCreate(source.url, UriKind.Absolute, out Uri url) && url.Scheme == Uri.UriSchemeHttps)
                {
                    view.Button(sources, "افتح المرجع • " + url.Host,
                        () => Application.OpenURL(url.AbsoluteUri), size: 17, height: 44);
                }
            }

            RectTransform actions = view.Row(body, "Project actions");
            view.Button(actions, "ابدأ التوصيل", () =>
            {
                assembling = selected;
                overlayVisible = true;
                step = 1;
                Show(Page.Tracking);
            }, true);
            view.Button(actions, "اعرض الكود", () => Show(Page.Sketch));
        }

        private void BuildTracking()
        {
            RectTransform headline = view.Card(body, "Tracking state");
            view.Label(headline, assembling == null ? "اختبار تثبيت الدائرة على البورد" : assembling.name_ar, 23);
            trackingStatus = view.Label(headline, previewMode ? "معاينة ثلاثية الأبعاد" : tracker.StatusArabic, 19, AppView.Mint);
            if (!previewMode)
                view.Label(headline, "ثبّت العلامة المطبوعة والبورد على حامل واحد، ثم وجّه الكاميرا نحو العلامة.", 17, AppView.Secondary);

            RectTransform stage = AppView.Rect(body, "Board view");
            AppView.Height(stage, 0, 1);
            if (previewMode)
            {
                preview ??= new AssemblyPreview(transform, catalog);
                preview.Show(assembling, step);
                RectTransform imageRect = AppView.Rect(stage, "Board image");
                AppView.Fill(imageRect);
                var image = imageRect.gameObject.AddComponent<RawImage>();
                image.texture = preview.Image;
                image.raycastTarget = false;
                var aspect = imageRect.gameObject.AddComponent<AspectRatioFitter>();
                aspect.aspectRatio = 1;
                aspect.aspectMode = AspectRatioFitter.AspectMode.FitInParent;
            }
            else
            {
                if (assembling == null)
                    assembly.ShowTrackingProof();
                else
                    assembly.ShowProject(assembling);
                assembly.ShowStep(step);
            }

            UpdateAssemblyVisibility();
            RectTransform controls = view.Card(body, "Board controls");
            if (assembling != null)
            {
                stepTitle = view.Label(controls, "", 19, AppView.Mint);
                stepInstruction = view.Label(controls, "", 18);
                RectTransform steps = view.Row(controls, "Step navigation");
                previousButton = view.Button(steps, "السابقة", () => MoveStep(-1), size: 18, height: 48);
                nextButton = view.Button(steps, "التالية", () => MoveStep(1), size: 18, height: 48);
                view.Button(steps, "كل الأسلاك", () => SetStep(0), size: 18, height: 48);
                view.Button(steps, "التفاصيل", () => Select(assembling), size: 18, height: 48);
                RefreshStep();
            }
            else
            {
                view.Label(controls, "LED ومقاومة وأسلاك معايرة. ابدؤوا واللوحة غير موصولة بالطاقة.", 18);
            }

            RectTransform modes = view.Row(controls, "Tracking modes");
            if (tracker != null && assembly != null && Application.platform == RuntimePlatform.Android)
            {
                view.Button(modes, previewMode ? "افتح الكاميرا" : "معاينة 3D", () =>
                {
                    previewMode = !previewMode;
                    Show(Page.Tracking);
                }, size: 18, height: 48);
            }
            Button calibration = view.Button(modes, "معايرة البورد", () => Show(Page.Calibration), size: 18, height: 48);
            calibration.interactable = tracker != null;
            Button visibility = null;
            visibility = view.Button(modes, VisibilityCaption(), () =>
            {
                overlayVisible = !overlayVisible;
                UpdateAssemblyVisibility();
                visibility.GetComponentInChildren<ArabicLabel>().SetContent(VisibilityCaption());
            }, size: 17, height: 48);
            if (assembling != null)
                view.Button(modes, "اختبار البورد", ResetProof, size: 17, height: 48);
        }

        private string VisibilityCaption() => overlayVisible ? "أخفِ المجسمات" : "أظهر المجسمات";

        private void UpdateAssemblyVisibility()
        {
            if (previewMode)
                preview.SetAssemblyVisible(overlayVisible);
            else
                assembly.SetAssemblyVisible(overlayVisible);
        }

        private void ResetProof()
        {
            assembling = null;
            overlayVisible = true;
            step = 0;
            Show(Page.Tracking);
        }

        private void MoveStep(int delta) => SetStep(CatalogNavigation.MoveStep(step, delta, assembling.assembly_steps.Length));

        private void SetStep(int value)
        {
            step = value;
            if (previewMode)
                preview.UpdateStep(step);
            else
                assembly.ShowStep(step);
            RefreshStep();
        }

        private void RefreshStep()
        {
            int count = assembling.assembly_steps.Length;
            stepTitle.SetContent(step == 0 ? "جميع التوصيلات" : $"الخطوة {step} / {count}");
            stepInstruction.SetContent(step == 0 ? "تظهر الآن كل أسلاك هذه الدائرة." :
                assembling.assembly_steps[step - 1].instruction_ar);
            previousButton.interactable = step == 0 || step > 1;
            nextButton.interactable = step == 0 || step < count;
        }

        private void BuildCalibration()
        {
            RectTransform settings = view.Scroll(body, "Calibration");
            RectTransform card = view.Card(settings, "Calibration values");
            view.Label(card, "المرجع وموقع البورد", 26, AppView.Mint);
            view.Label(card, "اطبع العلامة بالحجم الفعلي 100%. تأكد من أن أبعادها 75 × 60 مم. ثبّتها قرب البورد على حامل صلب بحيث يتحركان معًا.");
            view.Label(card, "قِس من مركز العلامة إلى مركز سطح البورد. المحور X نحو يمين العلامة، وY إلى أعلى سطحها، وZ نحو حافتها العليا.", 19, AppView.Secondary);
            InputField[] offset = VectorInputs(card, "الإزاحة بالملليمتر", tracker.Calibration.OffsetMillimetres);
            InputField[] euler = VectorInputs(card, "الدوران بالدرجات", tracker.Calibration.RotationDegrees);
            ArabicLabel status = view.Label(card, "", 18, AppView.Amber);

            RectTransform actions = view.Row(body, "Calibration actions");
            view.Button(actions, "طبّق وارجع", () =>
            {
                if (!TryVector(offset, out Vector3 movement) || !TryVector(euler, out Vector3 turning))
                {
                    status.SetContent("أدخل قيمة رقمية منتهية في كل حقل.");
                    return;
                }
                tracker.SetCalibration(movement, turning);
                Show(Page.Tracking);
            }, true);
            view.Button(actions, "أعد الضبط", () =>
            {
                tracker.SetCalibration(initialOffset, initialRotation);
                tracker.ResetTracking();
                Show(Page.Calibration);
            });
        }

        private InputField[] VectorInputs(RectTransform parent, string title, Vector3 current)
        {
            view.Label(parent, title, 21);
            RectTransform axes = view.Row(parent, title);
            var fields = new InputField[3];
            for (int axis = 0; axis < 3; ++axis)
            {
                RectTransform column = view.Stack(axes, ((char)('X' + axis)).ToString(), 4);
                view.Label(column, column.name, 19, AppView.Secondary, TextAnchor.MiddleCenter);
                fields[axis] = view.Input(column, current[axis].ToString("0.###", CultureInfo.InvariantCulture), "", true);
            }
            return fields;
        }

        private static bool TryVector(InputField[] fields, out Vector3 vector)
        {
            vector = Vector3.zero;
            for (int index = 0; index < 3; ++index)
            {
                if (!float.TryParse(fields[index].text, NumberStyles.Float, CultureInfo.InvariantCulture, out float value) ||
                    float.IsNaN(value) || float.IsInfinity(value))
                    return false;
                vector[index] = value;
            }
            return true;
        }

        private static string ReviewName(ProjectData project) =>
            project.verification?.status == "verified" ? "مُتحقق منه" : "مسودة تعليمية";

        private static string StepTerminals(ProjectData project, AssemblyStepData step)
        {
            return string.Join("\n", project.connections.Where(connection => step.connection_ids.Contains(connection.id))
                .Select(connection => $"{connection.from} → {connection.to}"));
        }

        private static string LevelName(string value)
        {
            switch (value)
            {
                case "beginner": return "مبتدئ";
                case "intermediate": return "متوسط";
                case "advanced": return "متقدم";
                default: return "الكل";
            }
        }

        private static string CategoryName(string value)
        {
            switch (value)
            {
                case "automation": return "الأتمتة";
                case "robotics": return "الروبوتات";
                case "environment": return "البيئة";
                case "measurement": return "القياس";
                case "control": return "التحكم";
                case "games": return "ألعاب تعليمية";
                case "education": return "أنشطة تعليمية";
                case "safety": return "السلامة التعليمية";
                case "access": return "التحكم في الدخول";
                case "display": return "العرض";
                case "timing": return "الوقت";
                case "monitoring": return "المراقبة";
                default: return string.IsNullOrEmpty(value) ? "الكل" : value;
            }
        }

        private void BuildSketch()
        {
            RectTransform heading = view.Card(body, "Sketch header");
            view.Label(heading, selected.name_ar, 23, AppView.Mint);
            view.Label(heading, selected.id + ".ino", 17, AppView.Secondary, TextAnchor.MiddleLeft);
            if (selected.required_libraries.Length > 0)
            {
                string requirements = string.Join(" • ", selected.required_libraries.Select(library =>
                    $"{library.name} {library.version}"));
                view.Label(heading, "المكتبات • " + requirements, 17);
            }

            try
            {
                sketch = CatalogLoader.LoadSketch(selected);
            }
            catch (InvalidOperationException error)
            {
                Debug.LogException(error, this);
                view.Label(body, "تعذر فتح ملف الكود المحلي.", 20, AppView.Amber);
                return;
            }

            RectTransform code = view.Scroll(body, "Scroll sketch");
            view.Code(view.Card(code, "Arduino sketch"), sketch);

            RectTransform footer = view.Card(body, "Sketch actions");
            sketchStatusLabel = view.Label(footer, sketchStatus ?? "", 17, AppView.Secondary);
            RectTransform primary = view.Row(footer, "Save and copy");
            saveButton = view.Button(primary, "نزّل ملف الكود", ExportSketch, true, 17, 48);
            view.Button(primary, "انسخ الكود", () =>
            {
                GUIUtility.systemCopyBuffer = sketch;
                SetSketchStatus("نُسخ الكود.");
            }, size: 17, height: 48);

            RectTransform secondary = view.Row(footer, "Open and share");
            openButton = view.Button(secondary, "افتح الملف", OpenSketch, size: 17, height: 48);
#if UNITY_ANDROID && !UNITY_EDITOR
            shareButton = view.Button(secondary, "شارك الملف", () => DocumentAction("share"), size: 17, height: 48);
#endif
            view.Button(secondary, "ارجع للمشروع", () => Show(Page.Project), size: 17, height: 48);
            RefreshSketchActions();
        }

        private void ExportSketch()
        {
            if (saving)
                return;
            pendingProject = selected.id;
            saving = true;
            RefreshSketchActions();

#if UNITY_ANDROID && !UNITY_EDITOR
            try
            {
                using var documents = new AndroidJavaClass(JavaDocuments);
                documents.CallStatic("save", gameObject.name, pendingProject + ".ino", sketch);
            }
            catch (AndroidJavaException error)
            {
                Debug.LogException(error, this);
                OnSketchDocumentResult("failed");
            }
#else
            try
            {
                string directory = Path.Combine(Application.persistentDataPath, "Arduino", pendingProject);
                Directory.CreateDirectory(directory);
                documentPath = Path.Combine(directory, pendingProject + ".ino");
                File.WriteAllText(documentPath, sketch, new UTF8Encoding(false));
                OnSketchDocumentResult("saved");
            }
            catch (Exception error) when (error is IOException || error is UnauthorizedAccessException)
            {
                Debug.LogException(error, this);
                OnSketchDocumentResult("failed");
            }
#endif
        }

        private void OpenSketch()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            DocumentAction("open");
#else
            if (!string.IsNullOrEmpty(documentPath))
                Application.OpenURL(new Uri(documentPath).AbsoluteUri);
#endif
        }

#if UNITY_ANDROID && !UNITY_EDITOR
        private void DocumentAction(string action)
        {
            try
            {
                using var documents = new AndroidJavaClass(JavaDocuments);
                documents.CallStatic(action, gameObject.name);
            }
            catch (AndroidJavaException error)
            {
                Debug.LogException(error, this);
                SetSketchStatus("تعذّر فتح الملف أو مشاركته.");
            }
        }
#endif

        [Preserve]
        public void OnSketchDocumentResult(string status)
        {
            saving = false;
            if (status == "saved")
                savedProject = pendingProject;
            pendingProject = null;
            switch (status)
            {
                case "saved": SetSketchStatus("تم حفظ ملف Arduino."); break;
                case "cancelled": SetSketchStatus("أُلغي الحفظ."); break;
                case "no_viewer": SetSketchStatus("لا يوجد تطبيق يمكنه فتح هذا الملف."); break;
                default: SetSketchStatus("تعذّر الوصول إلى الملف."); break;
            }
            RefreshSketchActions();
        }

        private void SetSketchStatus(string status)
        {
            sketchStatus = status;
            if (page == Page.Sketch && sketchStatusLabel != null)
                sketchStatusLabel.SetContent(status);
        }

        private void RefreshSketchActions()
        {
            if (page != Page.Sketch || saveButton == null || openButton == null)
                return;
            saveButton.interactable = !saving;
            bool canOpen = !saving && savedProject == selected.id;
            openButton.interactable = canOpen;
            if (shareButton != null)
                shareButton.interactable = canOpen;
        }
    }
}
