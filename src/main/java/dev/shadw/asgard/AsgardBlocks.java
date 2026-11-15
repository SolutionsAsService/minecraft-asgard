package dev.shadw.asgard;

import java.util.function.Function;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;

/** The blocks: the world tree's log and leaves, and the rune stone. Each has a block item. */
public final class AsgardBlocks {
	public static final Block YGGDRASIL_LOG = register("yggdrasil_log", key -> new RotatedPillarBlock(
			BlockBehaviour.Properties.of().strength(3.0F).sound(SoundType.WOOD).ignitedByLava().setId(key)));

	public static final Block YGGDRASIL_LEAVES = register("yggdrasil_leaves", key -> new YggdrasilLeavesBlock(
			BlockBehaviour.Properties.of().strength(0.2F).sound(SoundType.AZALEA_LEAVES).noOcclusion()
					.isValidSpawn((state, getter, pos, type) -> false)
					.isSuffocating((state, getter, pos) -> false)
					.isViewBlocking((state, getter, pos) -> false)
					.ignitedByLava().setId(key)));

	public static final Block RUNE_STONE = register("rune_stone", key -> new Block(
			BlockBehaviour.Properties.of().strength(2.0F, 6.0F).sound(SoundType.STONE)
					.requiresCorrectToolForDrops().setId(key)));

	/** The gold runes that wind up Yggdrasil's trunk: they glow. */
	public static final Block YGGDRASIL_RUNE = register("yggdrasil_rune", key -> new RuneGlowBlock(
			BlockBehaviour.Properties.of().strength(3.0F).sound(SoundType.WOOD).lightLevel(state -> 12).ignitedByLava().setId(key)));

	public static final Block YGGDRASIL_HEARTWOOD = register("yggdrasil_heartwood", key -> new Block(
			BlockBehaviour.Properties.of().strength(4.0F, 8.0F).sound(SoundType.WOOD).requiresCorrectToolForDrops().ignitedByLava().setId(key)));

	public static final Block ANCIENT_BARK = register("ancient_bark", key -> new Block(
			BlockBehaviour.Properties.of().strength(2.5F).sound(SoundType.WOOD).ignitedByLava().setId(key)));

	public static final Block GOLDEN_LEAVES = register("golden_leaves", key -> new GoldenLeavesBlock(
			BlockBehaviour.Properties.of().strength(0.2F).sound(SoundType.AZALEA_LEAVES).noOcclusion().lightLevel(state -> 9)
					.isValidSpawn((state, getter, pos, type) -> false)
					.isSuffocating((state, getter, pos) -> false)
					.isViewBlocking((state, getter, pos) -> false)
					.ignitedByLava().setId(key)));

	public static final String[] GODS = {"thor", "odin", "freyja", "loki", "freyr", "tyr", "heimdall"};
	public static final Block[] ALTARS = new Block[GODS.length];

	static {
		for (int i = 0; i < GODS.length; i++) {
			String god = GODS[i];
			ALTARS[i] = register(god + "_altar", key -> new AltarBlock(
					BlockBehaviour.Properties.of().strength(3.0F, 8.0F).sound(SoundType.STONE).requiresCorrectToolForDrops()
							.lightLevel(state -> 7).setId(key), god));
		}
	}

	private static int count;

	private AsgardBlocks() {}

	/** How many blocks this mod registers. */
	public static int count() {
		return count;
	}

	private static Block register(String path, Function<ResourceKey<Block>, Block> factory) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, ResourceLocation.fromNamespaceAndPath(Mod.MOD_ID, path));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(key));
		count++;
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, key.location());
		Registry.register(BuiltInRegistries.ITEM, itemKey,
				new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix()));
		return block;
	}

	/** Touching this class registers the blocks. */
	public static void init() {}
}
