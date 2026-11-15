package dev.shadw.asgard;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.ParrotRenderer;
import net.minecraft.client.renderer.entity.ZombieRenderer;
import net.minecraft.client.renderer.entity.state.ParrotRenderState;
import net.minecraft.client.renderer.entity.state.ZombieRenderState;
import net.minecraft.resources.ResourceLocation;

/** Client side: the creatures reuse the zombie and parrot models with their own skins. */
public class AsgardClient implements ClientModInitializer {
	private static ResourceLocation texture(String name) {
		return ResourceLocation.fromNamespaceAndPath(Mod.MOD_ID, "textures/entity/" + name + ".png");
	}

	/** A zombie-shaped creature with its own skin. */
	static class SkinnedZombieRenderer extends ZombieRenderer {
		private final ResourceLocation skin;

		SkinnedZombieRenderer(EntityRendererProvider.Context context, ResourceLocation skin) {
			super(context);
			this.skin = skin;
		}

		@Override
		public ResourceLocation getTextureLocation(ZombieRenderState state) {
			return skin;
		}
	}

	static class RavenRenderer extends ParrotRenderer {
		private static final ResourceLocation SKIN = texture("raven");

		RavenRenderer(EntityRendererProvider.Context context) {
			super(context);
		}

		@Override
		public ResourceLocation getTextureLocation(ParrotRenderState state) {
			return SKIN;
		}
	}

	@Override
	public void onInitializeClient() {
		EntityRendererRegistry.register(AsgardEntities.DRAUGR, ctx -> new SkinnedZombieRenderer(ctx, texture("draugr")));
		EntityRendererRegistry.register(AsgardEntities.TROLL, ctx -> new SkinnedZombieRenderer(ctx, texture("troll")));
		EntityRendererRegistry.register(AsgardEntities.RAVEN, RavenRenderer::new);
	}
}
