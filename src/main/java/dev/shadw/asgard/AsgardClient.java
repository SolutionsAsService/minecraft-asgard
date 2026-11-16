package dev.shadw.asgard;

import dev.shadw.asgard.mobs.GeneratedMobsClient;
import net.fabricmc.api.ClientModInitializer;

/** Client side: every creature has its own model, registered by the generated GeneratedMobsClient (the raven included). */
public class AsgardClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		GeneratedMobsClient.initClient();
	}
}
