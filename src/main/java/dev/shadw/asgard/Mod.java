package dev.shadw.asgard;

import com.google.gson.JsonArray;
import dev.shadw.asgard.mobs.GeneratedMobs;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.registry.FabricBrewingRecipeRegistryBuilder;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.alchemy.Potion;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.item.crafting.Ingredient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Asgard. Every potion is data: potions.json lists the realm, the
 * ingredient, the lore and the effects. Adding a potion means adding an entry
 * and running tools/gen_assets.py. Unknown effect ids are logged and skipped.
 */
public class Mod implements ModInitializer {
	public static final String MOD_ID = "asgard";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private record Pending(Item ingredient, Holder<Potion> potion) {}

	@Override
	public void onInitialize() {
		AsgardBlocks.init();
		AsgardItems.init();
		AsgardEntities.init();
		GeneratedMobs.init();
		JsonObject root = load();
		JsonArray potions = root.getAsJsonArray("potions");
		List<Pending> pending = new ArrayList<>();
		int effectsSkipped = 0;

		for (JsonElement element : potions) {
			JsonObject entry = element.getAsJsonObject();
			String id = entry.get("id").getAsString();
			String ingredient = entry.get("ingredient").getAsString();
			String lore = "item." + MOD_ID + "." + ingredient + ".lore";

			Item item = Registry.register(BuiltInRegistries.ITEM,
					ResourceLocation.fromNamespaceAndPath(MOD_ID, ingredient),
					new LoreItem(new Item.Properties().setId(itemKey(ingredient)), lore));

			List<MobEffectInstance> effects = new ArrayList<>();
			for (JsonElement e : entry.getAsJsonArray("effects")) {
				JsonObject eff = e.getAsJsonObject();
				String effectId = eff.get("effect").getAsString();
				Holder<MobEffect> holder = effectHolder(effectId);
				if (holder == null) {
					LOGGER.warn("Potion '{}': unknown effect '{}', skipped", id, effectId);
					effectsSkipped++;
					continue;
				}
				int ticks = eff.get("seconds").getAsInt() * 20;
				int amplifier = eff.get("amplifier").getAsInt();
				effects.add(new MobEffectInstance(holder, ticks, amplifier));
			}

			ResourceKey<Potion> potionKey = ResourceKey.create(Registries.POTION,
					ResourceLocation.fromNamespaceAndPath(MOD_ID, id));
			Holder<Potion> potion = Registry.registerForHolder(BuiltInRegistries.POTION, potionKey,
					new Potion(id, effects.toArray(new MobEffectInstance[0])));
			pending.add(new Pending(item, potion));
		}

		int fromData = pending.size();
		pending.add(new Pending(AsgardItems.YGGDRASIL_LEAF, AsgardItems.BLESSING));

		FabricBrewingRecipeRegistryBuilder.BUILD.register(builder -> {
			for (Pending p : pending) {
				builder.registerPotionRecipe(Potions.AWKWARD, Ingredient.of(p.ingredient()), p.potion());
			}
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.INGREDIENTS).register(entries -> {
			for (Pending p : pending) {
				entries.accept(p.ingredient());
			}
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.NATURAL_BLOCKS).register(entries -> {
			entries.accept(AsgardBlocks.YGGDRASIL_LOG);
			entries.accept(AsgardBlocks.YGGDRASIL_LEAVES);
			entries.accept(AsgardBlocks.YGGDRASIL_RUNE);
			entries.accept(AsgardBlocks.GOLDEN_LEAVES);
			entries.accept(AsgardBlocks.ANCIENT_BARK);
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.BUILDING_BLOCKS).register(entries -> {
			entries.accept(AsgardBlocks.RUNE_STONE);
			entries.accept(AsgardBlocks.YGGDRASIL_HEARTWOOD);
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.SPAWN_EGGS).register(entries -> {
			GeneratedMobs.EGGS.forEach(entries::accept);
			entries.accept(AsgardEntities.RAVEN_SPAWN_EGG);
			entries.accept(AsgardEntities.SLEIPNIR_SPAWN_EGG);
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.FUNCTIONAL_BLOCKS).register(entries -> {
			for (var altar : AsgardBlocks.ALTARS) {
				entries.accept(altar);
			}
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.COMBAT).register(entries -> {
			entries.accept(AsgardItems.MJOLNIR);
			entries.accept(AsgardItems.GUNGNIR);
		});
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.TOOLS_AND_UTILITIES)
				.register(entries -> entries.accept(AsgardItems.GJALLARHORN));
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.FOOD_AND_DRINKS)
				.register(entries -> entries.accept(AsgardItems.YGGDRASIL_FRUIT));
		ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.INGREDIENTS).register(entries -> {
			entries.accept(AsgardItems.YGGDRASIL_SAP);
			entries.accept(AsgardItems.SACRED_ROOT);
		});
		LOGGER.info("Asgard loaded: {} potions ({} from data, plus Blessing), {} brewing recipes, {} unknown effects skipped; "
				+ "3 relics, {} blocks, {} creatures", pending.size(), fromData, pending.size(), effectsSkipped, AsgardBlocks.count(), GeneratedMobs.EGGS.size() + 2);
	}

	private static ResourceKey<Item> itemKey(String path) {
		return ResourceKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath(MOD_ID, path));
	}

	private static Holder<MobEffect> effectHolder(String id) {
		ResourceLocation location = ResourceLocation.parse(id);
		return BuiltInRegistries.MOB_EFFECT.getOptional(location)
				.map(BuiltInRegistries.MOB_EFFECT::wrapAsHolder)
				.orElse(null);
	}

	private static JsonObject load() {
		String path = "/assets/" + MOD_ID + "/potions.json";
		try (InputStream stream = Mod.class.getResourceAsStream(path)) {
			if (stream == null) {
				throw new IllegalStateException("missing " + path);
			}
			return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (java.io.IOException e) {
			throw new IllegalStateException("cannot read " + path, e);
		}
	}
}
