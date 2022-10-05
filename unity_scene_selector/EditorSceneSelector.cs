using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEngine;
using System.Collections.Generic;
using Newtonsoft.Json;
using System.Linq;


public class EditorSceneSelector : EditorWindow {
    private static EditorSceneSelector window;

    private string userDefinedProjectScenePath = "Assets/";
    private string userDefinedSceneNameGroups = "";
    private string filename = "EditorSceneSelectorConfigData.json";
    private static string uncategorizedGroup = "emptyList";
    private Dictionary<string, List<string>> categorizedScenesDict = new Dictionary<string, List<string>>();

    private static float mainWindowHeight = 150;
    private static float mainWindowWidth = 100;
    private int buttonHeight = 20;
    private int buttonWidth = 54;

    private Vector2 scrollPos;
    private Color separatorColor = new Color(0.964f, 0.8039f, 0.380f);

    private Color lineColorGray = new Color(1.0f, 0.913f, 0.862f);
    private Texture2D lineTextureGray;
    private GUIStyle lineStyleGray;
    private Color lineColorGreen = new Color(0.658f, 0.901f, 0.811f);
    private Texture2D lineTextureGreen;
    private GUIStyle lineStyleGreen;
    private Color lineColorRed = new Color(1.0f, 0.435f, 0.411f);
    private Texture2D lineTextureRed;
    private GUIStyle lineStyleRed;

    private Rect headerSection;
    private Rect bodySection;
    private Rect lineSection;
    private string[] sceneGuids;

    private List<string> sceneList = new List<string>();
    private List<string> locationSceneList = new List<string>();
    private List<string> testSceneList = new List<string>();

    private List<string> loadedScenes = new List<string>();

    private bool dirtyData = false;
    private bool showConfiguration = false;

    private EditorSceneSelectorConfigData configurationData = new EditorSceneSelectorConfigData();
    private List<string> currentSceneNameGroups = new List<string>();


    [MenuItem("Juniper/Scene selector %#o")] // %#o - CTRL + SHIFT + o
    private static void OpenWindow() {
        window = GetWindow<EditorSceneSelector>();
        // window.minSize = new Vector2(mainWindowWidth, mainWindowHeight);
    }

    private void OnEnable() {
        sceneGuids = AssetDatabase.FindAssets("t:Scene");
        InitConfigurationData();
        GetLoadedScenes();
        PrepareEditorSceneSelectorData();
    }

    private void InitConfigurationData() {
        string tempEditorDirectory = Path.Combine(Application.persistentDataPath, "Editor");
        string fullPath = GetPathToFile(filename);

        if (!FileAndDirectoryExists(tempEditorDirectory) || !File.Exists(fullPath)) {
            Directory.CreateDirectory(tempEditorDirectory);
            try {
                configurationData.projectScenePath = "Assets/";
                configurationData.sceneNameGroups = "";
                WriteToFile(fullPath);
            } catch (System.Exception e) {
                Debug.LogError($"Failed to write to {fullPath} with exception {e}");
            }
        }

        if (ReadFromFile(filename, out string json)) {
            EditorSceneSelectorConfigData loadedData = new EditorSceneSelectorConfigData();
            loadedData = JsonConvert.DeserializeObject<EditorSceneSelectorConfigData>(json);

            configurationData.projectScenePath = loadedData.projectScenePath;
            configurationData.sceneNameGroups = loadedData.sceneNameGroups;
        }
    }

    private void OnGUI() {
        SetupGUIStyles();
        DrawLayouts();
        DrawItems();
    }

    private void SetupGUIStyles() {
        lineTextureGray = new Texture2D(1, 1);
        lineTextureGray.SetPixel(0, 0, lineColorGray);
        lineTextureGray.Apply();

        lineStyleGray = new GUIStyle(GUI.skin.label);
        lineStyleGray.normal.textColor = Color.black;
        lineStyleGray.normal.background = lineTextureGray;


        lineTextureGreen = new Texture2D(1, 1);
        lineTextureGreen.SetPixel(0, 0, lineColorGreen);
        lineTextureGreen.Apply();

        lineStyleGreen = new GUIStyle(GUI.skin.label);
        lineStyleGreen.fontStyle = FontStyle.Bold;
        lineStyleGreen.normal.textColor = Color.black;
        lineStyleGreen.normal.background = lineTextureGreen;

        lineTextureRed = new Texture2D(1, 1);
        lineTextureRed.SetPixel(0, 0, lineColorRed);
        lineTextureRed.Apply();

        lineStyleRed = new GUIStyle(GUI.skin.label);
        lineStyleRed.normal.textColor = Color.black;
        lineStyleRed.normal.background = lineTextureRed;
    }

    private void DrawLayouts() {
        mainWindowHeight = position.height;
        mainWindowWidth = position.width;

        bodySection.x = 0;
        bodySection.y = 0;
        bodySection.width = Screen.width;
        bodySection.height = Screen.height;
    }

    private void DrawItems() {
        if (dirtyData) {
            PrepareEditorSceneSelectorData();
            if (window != null) window.Close();
            OpenWindow();
            GetLoadedScenes();
            dirtyData = false;
        }

        GUILayout.BeginArea(bodySection);
        scrollPos = EditorGUILayout.BeginScrollView(scrollPos, GUILayout.Width(mainWindowWidth), GUILayout.Height(mainWindowHeight));

        string activeScene = SceneManager.GetActiveScene().name;

        foreach (var item in categorizedScenesDict) {
            DrawGUILine(separatorColor);

            for (int i = 0; i < item.Value.Count; i++) {  // sceneNameGroups
                EditorGUILayout.BeginHorizontal();

                int index = item.Value[i].LastIndexOf("/") + 1;
                string sceneNameToLoad = item.Value[i].Substring(index, item.Value[i].Length - index).Split(".")[0];

                if (System.String.Equals(activeScene, sceneNameToLoad)) {
                    if (GUILayout.Button("ACTIVE", lineStyleGreen, GUILayout.Height(buttonHeight), GUILayout.Width(buttonWidth))) {};
                    GUILayout.Label($"{sceneNameToLoad}", lineStyleGreen, GUILayout.Height(buttonHeight));
                } else if (loadedScenes.Contains(sceneNameToLoad)) {
                    if (GUILayout.Button("", lineStyleGreen, GUILayout.Height(buttonHeight), GUILayout.Width(8))) { SetActiveSceneButton(sceneNameToLoad); };
                    if (GUILayout.Button("ADDED", lineStyleGray, GUILayout.Height(buttonHeight), GUILayout.Width(buttonWidth))) {};
                    GUILayout.Label($"{sceneNameToLoad}", lineStyleGray, GUILayout.Height(buttonHeight));
                    if (GUILayout.Button("UNLOAD", lineStyleRed, GUILayout.Height(buttonHeight), GUILayout.Width(buttonWidth))) { UnloadSceneButton(sceneNameToLoad); };
                } else {
                    if (GUILayout.Button("OPEN", GUILayout.Height(buttonHeight), GUILayout.Width(buttonWidth)))
                        OpenSceneButton(item.Value[i]);
                    if (GUILayout.Button("ADD", GUILayout.Height(buttonHeight), GUILayout.Width(buttonWidth)))
                        OpenSceneButton(item.Value[i], true);

                    GUILayout.Label($"{sceneNameToLoad}", GUILayout.Height(buttonHeight));
                }
                EditorGUILayout.EndHorizontal();
            }
        }

        DrawConfiguration();

        EditorGUILayout.EndScrollView();
        GUILayout.EndArea();
    }

    private void DrawConfiguration() {
        EditorGUILayout.Space();
        showConfiguration = EditorGUILayout.Foldout(showConfiguration, "CONFIGURATION", true);

        if (showConfiguration) {
            if (configurationData.projectScenePath.Length > 0) {
                userDefinedProjectScenePath = configurationData.projectScenePath;
                userDefinedSceneNameGroups = System.String.Join(", ", configurationData.sceneNameGroups);
            }

            EditorGUILayout.BeginHorizontal();
            GUILayout.Label($"Project scene path:", GUILayout.Height(buttonHeight));
            configurationData.projectScenePath = EditorGUILayout.TextField($"{userDefinedProjectScenePath}", GUILayout.Height(buttonHeight));
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.BeginHorizontal();
            GUILayout.Label($"Scene categories", GUILayout.Height(buttonHeight));
            configurationData.sceneNameGroups = EditorGUILayout.TextField(userDefinedSceneNameGroups);
            EditorGUILayout.EndHorizontal();

            if (GUILayout.Button("SAVE CHANGES", GUILayout.Height(buttonHeight))) SaveConfiguration();
        }
    }

    private void SaveConfiguration() {
        string fullPath = GetPathToFile(filename);
        WriteToFile(fullPath);
        dirtyData = true;
    }

    private void OpenSceneButton(string scenePath, bool asAdditive = false) {
        if (asAdditive) EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Additive);
        else EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
        dirtyData = true;
    }

    private void UnloadSceneButton(string scenePath) {
        EditorSceneManager.CloseScene(SceneManager.GetSceneByName(scenePath), true);
        dirtyData = true;
    }

    private void SetActiveSceneButton(string scenePath) {
        EditorSceneManager.SetActiveScene(SceneManager.GetSceneByName(scenePath));
        dirtyData = true;
    }

    private List<string> GetScenesWithPrefix(List<string> allScenes, string prefix) {
        List<string> tempScenesList = new List<string>();

        for (int i = 0; i < allScenes.Count; i++) {
            int index = allScenes[i].LastIndexOf("/") + 1;
            string sceneNameToLoad = allScenes[i].Substring(index, allScenes[i].Length - index).Split(".")[0];
            if (sceneNameToLoad.StartsWith(prefix)) tempScenesList.Add(allScenes[i]);
        }

        return tempScenesList;
    }

    private void PrepareEditorSceneSelectorData() {
        categorizedScenesDict.Clear();

        currentSceneNameGroups = configurationData.sceneNameGroups.Split(',').ToList();

        // Create a List of all scenes that are in project/scene folder
        List<string> tempSceneAssetList = new List<string>();
        foreach (var sceneGuid in sceneGuids) {
            string scenePath = AssetDatabase.GUIDToAssetPath(sceneGuid);
            if (scenePath.StartsWith(configurationData.projectScenePath)) {
                Object sceneAsset = AssetDatabase.LoadAssetAtPath(scenePath, typeof(SceneAsset));
                tempSceneAssetList.Add(scenePath.ToString());
            }
        }

        // Create an empty Lists of all user defined scene categories and add them to Dictionary
        List<string> emptyList = new List<string>();
        for (int x = 0; x < currentSceneNameGroups.Count; x++) {
            categorizedScenesDict.Add(currentSceneNameGroups[x], emptyList);
        }

        // Categorize all scenes to their proper categories
        List<string> uncategorizedList = new List<string>();
        for (int i = 0; i < currentSceneNameGroups.Count; i++) {
            List<string> tempCategorized = GetScenesWithPrefix(tempSceneAssetList, currentSceneNameGroups[i].ToString());
            categorizedScenesDict[currentSceneNameGroups[i]] = tempCategorized;
            uncategorizedList.AddRange(tempCategorized);
        }

        // Separate all uncategorized scenes and add them to Uncategorized group.
        currentSceneNameGroups.Add(uncategorizedGroup);
        categorizedScenesDict[uncategorizedGroup] = tempSceneAssetList.Except(uncategorizedList).ToList();
    }

    private void GetLoadedScenes() {
        loadedScenes.Clear();
        int countLoaded = SceneManager.sceneCount;

        for (int i = 0; i < countLoaded; i++) {
            loadedScenes.Add(SceneManager.GetSceneAt(i).name);
        }
    }

    private void DrawGUILine(Color color, int thickness = 4, int padding = 6) {
        Rect r = EditorGUILayout.GetControlRect(GUILayout.Height(padding + thickness));
        EditorGUI.DrawRect(r, color);
    }

    private bool FileAndDirectoryExists(string tempEditorDirectory) {
        if (Directory.Exists(tempEditorDirectory)) return true;
        return false;
    }

    private void WriteToFile(string fullPath) {
        string data = JsonUtility.ToJson(configurationData, true);
        File.WriteAllText(fullPath, data);
    }

    private bool ReadFromFile(string filename, out string result) {
        string fullPath = GetPathToFile(filename);

        try {
            result = File.ReadAllText(fullPath);
            return true;
        } catch (System.Exception e) {
            Debug.LogError($"Failed to read from {fullPath} with exception {e}");
            result = "";
            return false;
        }
    }

    private static string GetPathToFile(string filename) {
        string path;
        try {
            return path = Path.Combine(Application.persistentDataPath, "Editor", filename);
        } catch (System.Exception e) {
            Debug.LogError($"{e}");
            return null;
        }
    }
}

public class EditorSceneSelectorConfigData {
    public string projectScenePath;
    public string sceneNameGroups;
}