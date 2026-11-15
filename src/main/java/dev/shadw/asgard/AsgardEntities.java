package dev.shadw.asgard;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricEntityType;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.levelgen.Heightmap;

/** The creatures: the draugr, the troll and Odin's raven, each with a spawn egg and natural spawns. */
public final class AsgardEntities {
	public static final EntityType<Draugr> DRAUGR = register("draugr", FabricEntityType.Builder.createMob(Draugr::new, MobCategory.MONSTER,
			b -> b.spawnRestriction(SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Monster::checkMonsterSpawnRules)
					.defaultAttributes(Draugr::createAttributes)).sized(0.6F, 1.95F).clientTrackingRange(8));

	public static final EntityType<Troll> TROLL = register("troll", FabricEntityType.Builder.createMob(Troll::new, MobCategory.MONSTER,
			b -> b.spawnRestriction(SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Monster::checkMonsterSpawnRules)
					.defaultAttributes(Troll::createAttributes)).sized(0.6F, 1.95F).clientTrackingRange(10));

	public static final EntityType<Raven> RAVEN = register("raven", FabricEntityType.Builder.createMob(Raven::new, MobCategory.CREATURE,
			b -> b.spawnRestriction(SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING, Animal::checkAnimalSpawnRules)
					.defaultAttributes(Raven::createAttributes)).sized(0.5F, 0.9F).clientTrackingRange(8));

	public static final Item DRAUGR_SPAWN_EGG = egg("draugr_spawn_egg", DRAUGR);
	public static final Item TROLL_SPAWN_EGG = egg("troll_spawn_egg", TROLL);
	public static final Item RAVEN_SPAWN_EGG = egg("raven_spawn_egg", RAVEN);

	private AsgardEntities() {}

	private static <T extends net.minecraft.world.entity.Entity> EntityType<T> register(String path, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, ResourceLocation.fromNamespaceAndPath(Mod.MOD_ID, path));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	private static Item egg(String path, EntityType<? extends net.minecraft.world.entity.Mob> type) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath(Mod.MOD_ID, path));
		return Registry.register(BuiltInRegistries.ITEM, key, new SpawnEggItem(type, new Item.Properties().setId(key)));
	}

	/** Registers the entity types and their natural spawns. */
	public static void init() {
		BiomeModifications.addSpawn(BiomeSelectors.tag(BiomeTags.IS_TAIGA).or(BiomeSelectors.tag(BiomeTags.IS_FOREST))
				.or(BiomeSelectors.tag(BiomeTags.IS_MOUNTAIN)), MobCategory.MONSTER, DRAUGR, 14, 1, 3);
		BiomeModifications.addSpawn(BiomeSelectors.tag(BiomeTags.IS_MOUNTAIN).or(BiomeSelectors.tag(BiomeTags.IS_TAIGA)),
				MobCategory.MONSTER, TROLL, 4, 1, 1);
		BiomeModifications.addSpawn(BiomeSelectors.tag(BiomeTags.IS_TAIGA).or(BiomeSelectors.tag(BiomeTags.IS_FOREST))
				.or(BiomeSelectors.tag(BiomeTags.IS_MOUNTAIN)), MobCategory.CREATURE, RAVEN, 6, 2, 4);
	}
}
