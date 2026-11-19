package com.mechavision.documents;

import android.app.Activity;
import android.app.Fragment;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

import com.unity3d.player.UnityPlayer;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public final class SketchDocuments extends Fragment {
    private static final String TAG = "MechaVisionSketchDocuments";
    private static final int CREATE_SKETCH = 7021;
    private String receiver;
    private String pendingSketch;
    private Uri savedDocument;

    public static void save(String receiver, String name, String sketch) {
        Activity activity = UnityPlayer.currentActivity;
        if (activity == null) {
            notifyUnity(receiver, "failed");
            return;
        }

        activity.runOnUiThread(() -> {
            SketchDocuments fragment = (SketchDocuments) activity.getFragmentManager().findFragmentByTag(TAG);
            if (fragment == null) {
                fragment = new SketchDocuments();
                activity.getFragmentManager().beginTransaction().add(fragment, TAG).commitNow();
            }
            fragment.chooseFile(receiver, name, sketch);
        });
    }

    public static void open(String receiver) {
        Activity activity = UnityPlayer.currentActivity;
        if (activity == null) {
            notifyUnity(receiver, "failed");
            return;
        }

        activity.runOnUiThread(() -> {
            SketchDocuments fragment = (SketchDocuments) activity.getFragmentManager().findFragmentByTag(TAG);
            if (fragment == null || fragment.savedDocument == null) {
                notifyUnity(receiver, "failed");
                return;
            }
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(fragment.savedDocument, "text/plain");
            intent.setClipData(ClipData.newRawUri("Arduino sketch", fragment.savedDocument));
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            try {
                activity.startActivity(intent);
            } catch (ActivityNotFoundException error) {
                notifyUnity(receiver, "no_viewer");
            } catch (SecurityException error) {
                notifyUnity(receiver, "failed");
            }
        });
    }

    public static void share(String receiver) {
        Activity activity = UnityPlayer.currentActivity;
        if (activity == null) {
            notifyUnity(receiver, "failed");
            return;
        }

        activity.runOnUiThread(() -> {
            SketchDocuments fragment = (SketchDocuments) activity.getFragmentManager().findFragmentByTag(TAG);
            if (fragment == null || fragment.savedDocument == null) {
                notifyUnity(receiver, "failed");
                return;
            }
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("text/plain");
            send.putExtra(Intent.EXTRA_STREAM, fragment.savedDocument);
            send.setClipData(ClipData.newRawUri("Arduino sketch", fragment.savedDocument));
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            try {
                activity.startActivity(Intent.createChooser(send, "مشاركة ملف Arduino"));
            } catch (ActivityNotFoundException | SecurityException error) {
                notifyUnity(receiver, "failed");
            }
        });
    }

    private void chooseFile(String destination, String name, String sketch) {
        receiver = destination;
        pendingSketch = sketch;
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        // A generic type lets DocumentsUI retain the .ino suffix.
        intent.setType("application/octet-stream");
        intent.putExtra(Intent.EXTRA_TITLE, name);
        try {
            startActivityForResult(intent, CREATE_SKETCH);
        } catch (ActivityNotFoundException | SecurityException error) {
            pendingSketch = null;
            notifyUnity(receiver, "failed");
        }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) {
            receiver = state.getString("receiver");
            pendingSketch = state.getString("sketch");
            savedDocument = state.getParcelable("document");
        }
    }

    @Override public void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putString("receiver", receiver);
        state.putString("sketch", pendingSketch);
        state.putParcelable("document", savedDocument);
    }

    @Override public void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != CREATE_SKETCH || receiver == null)
            return;

        String sketch = pendingSketch;
        pendingSketch = null;
        if (resultCode != Activity.RESULT_OK || data == null) {
            notifyUnity(receiver, "cancelled");
            return;
        }

        Uri uri = data.getData();
        Activity activity = getActivity();
        if (uri == null || sketch == null || activity == null) {
            notifyUnity(receiver, "failed");
            return;
        }

        try (OutputStream output = activity.getContentResolver().openOutputStream(uri, "wt")) {
            if (output == null)
                throw new IOException("The document provider did not supply a writable stream.");
            output.write(sketch.getBytes(StandardCharsets.UTF_8));
        } catch (IOException | SecurityException error) {
            Log.w(TAG, "Unable to write the sketch.", error);
            notifyUnity(receiver, "failed");
            return;
        }

        savedDocument = uri;
        notifyUnity(receiver, "saved");
    }

    private static void notifyUnity(String receiver, String status) {
        UnityPlayer.UnitySendMessage(receiver, "OnSketchDocumentResult", status);
    }
}
