package com.exadprinter.fingerprintinglib

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONException
import java.io.BufferedReader
import java.io.IOException
import java.io.InputStreamReader

private const val TAG: String = "ClassesJsonReader"
private const val CLASSES_LIST_PATH: String = "classes.json"
class ClassesJsonReader {
    /**
     * Reads a JSON array from a file in the assets folder and converts it to a list of strings.
     *
     * @param context  The application context.
     * @return A list of strings parsed from the JSON array in the file, or an empty list if an error occurs.
     */
    suspend fun readJsonFromAssets(context: Context): ArrayList<String> {
        val jsonString = loadJSONFromAsset(context)
        if (jsonString != null) {
            try {
                val jsonArray = JSONArray(jsonString)
                val stringArray = ArrayList<String>()
                for (i in 0 until jsonArray.length()) {
                    stringArray.add(jsonArray.getString(i))
                }
                return stringArray
            } catch (e: JSONException) {
                Log.e(TAG, "Error reading JSON from assets", e)
                return ArrayList()
            }
        }
        return ArrayList()
    }

    /**
     * Loads a JSON string from a file in the assets folder.
     *
     * @param context  The application context.
     * @return The JSON string read from the file, or null if an error occurs.
     */
    private suspend fun loadJSONFromAsset(context: Context): String? = withContext(Dispatchers.IO) {
        val json: String
        try {
            val assetManager = context.assets
            val inputStream = assetManager.open(CLASSES_LIST_PATH)
            val bufferedReader = BufferedReader(InputStreamReader(inputStream))
            val stringBuilder = StringBuilder()
            var line: String?
            while (bufferedReader.readLine().also { line = it } != null) {
                stringBuilder.append(line)
            }
            bufferedReader.close()
            inputStream.close()
            json = stringBuilder.toString()
        } catch (e: IOException) {
            Log.e(TAG, "Error reading JSON from assets", e)
            return@withContext null
        }
        return@withContext json
    }
}
